import requests
import json
import logging
import os
import http.client as http_client
import sys
from io import StringIO

# Setup basic configuration for logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


class HTTPDebugLogHandler(StringIO):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.buffer = ""  # Initialize a buffer to accumulate log messages

    def write(self, message):
        """
        Override the write function to accumulate messages until a complete message is ready to be logged.
        """
        # Append the message to the buffer
        self.buffer += message

        # Check if the buffer ends with a complete HTTP message (simplified check)
        if "\n\n" in self.buffer or "\r\n\r\n" in self.buffer:
            # Here you can format the message as you wish
            formatted_message = self.buffer.replace("\\r\\n", "\n").rstrip()  # Replace \r\n with \n
            self.logger.debug(formatted_message)
            self.buffer = ""  # Clear the buffer after logging

    def flush(self):
        """
        Override the flush function to handle any flushing operations.
        If there's any remaining message in the buffer, log it.
        """
        if self.buffer.rstrip():
            self.logger.debug(self.buffer.replace("\\r\\n", "\n").rstrip())
            self.buffer = ""  # Clear the buffer


# Redirect stdout to capture http.client's output
http_debug_logger = logging.getLogger("http.client.debug")
sys.stdout = HTTPDebugLogHandler(http_debug_logger)

# Enable HTTP request logging
http_client.HTTPConnection.debuglevel = 1


# Function to load credentials from fixed_credentials.json
def load_credentials():
    credentials_path = "your-details.json"
    if os.path.exists(credentials_path):
        with open(credentials_path, "r", encoding="utf-8") as file:
            credentials = json.load(file)
            return credentials
    return {}


def make_post_request(url, post_headers, post_data):
    """
    Make a POST request to the server with headers and data
    """
    try:
        post_response = requests.post(url, headers=post_headers, data=post_data, timeout=10)
        post_response.raise_for_status()  # Raises an HTTPError if the response status code is 4XX or 5XX
        response_json = post_response.json()
        logging.info(f"Response JSON: {response_json}")  # Debugging line to print the response
        logging.info(f"Response Headers: {post_response.headers}")  # Log the response headers
        return response_json
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")  # Python 3.6+
    except Exception as err:
        logging.error(f"An error occurred: {err}")  # Python 3.6+
    return {}  # Return an empty dictionary in case of error


# TODO: Figure out how to generate these correctly!
# For now, grab them from browser session...
imprint_device_id = "???"
imprint_signature = "???"

# Base headers
base_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "*/*",
    "Accept-Language": "en-US",
    "Accept-Encoding": "gzip, deflate, br",
    "x-imprint-signature": imprint_signature,
    "x-imprint-device-id": imprint_device_id,
    "x-imprint-platform": "web",
    "Content-Type": "text/plain;charset=UTF-8",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Origin": "https://account.imprint.co",
    "Referer": "https://account.imprint.co/",
    "TE": "trailers",
}

# Load or prompt for phone number
credentials = load_credentials()
phone_number = credentials.get("phone_number")
if not phone_number:
    phone_number = input("Enter your phone number (to avoid typing this every time, add it to your-details.json): ")

raw_post_data = '{"phone":"' + phone_number + '","resend":false}'
response = make_post_request("https://api.imprint.co/v1/consumer/login", base_headers, raw_post_data)
request_id = response["requestID"]

# Prompt user for OTP code and send it to the server
otp_code = input("Enter the OTP code you received: ")
raw_post_data = '{"requestId":"' + request_id + '","code":"' + otp_code + '"}'

response = make_post_request("https://api.imprint.co/v2/consumer/login/otp", base_headers, raw_post_data)
request_id = response["requestID"]

# Load or prompt for PIN
pin = credentials.get("pin")
if not pin:
    pin = input("Enter your PIN (to avoid typing this every time, add it to your-details.json): ")

raw_post_data = '{"pin":"' + pin + '","requestID":"' + request_id + '"}'
response = make_post_request("https://api.imprint.co/v1/consumer/mfa/pin", base_headers, raw_post_data)
token = response["token"]

# Save the token to token.json
with open("credentials.json", "w", encoding="utf-8") as file:
    json.dump({"imprint_access_token": token, "imprint_device_id": imprint_device_id, "imprint_signature": imprint_signature}, file)

print("Credentials saved to credentials.json")
