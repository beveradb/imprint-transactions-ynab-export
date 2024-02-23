import requests
import json
import csv
import logging

# Setup basic configuration for logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load API credentials, which should contain three values from a logged-in session (from browser dev tools, or using interactive-login.py):
# imprint_access_token, imprint_device_id, imprint_signature
with open("credentials.json", encoding="utf-8") as f:
    credentials = json.load(f)

imprint_access_token = credentials["imprint_access_token"]
imprint_device_id = credentials["imprint_device_id"]
imprint_signature = credentials["imprint_signature"]
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Accept": "*/*",
    "Accept-Language": "en-US",
    "Accept-Encoding": "gzip, deflate, br",
    "x-imprint-signature": imprint_signature,
    "x-imprint-device-id": imprint_device_id,
    "x-imprint-access-token": imprint_access_token,
    "x-imprint-platform": "WEB",
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

post_data = '{"filters":{"productAccountUUIDs":["PACT-v1-61c8703c-ff92-4172-a7ad-be687fb2ebb3"],"transactionTypesAndStatuses":[{"type":"AUTH","statuses":["PENDING"]},{"type":"TRANSACTION","statuses":["CONFIRMED","REJECTED","CANCELED"]},{"type":"DISPUTE","statuses":["CONFIRMED","REJECTED","CANCELED","PENDING"]},{"type":"PAYMENT","statuses":["SCHEDULED","PENDING","CONFIRMED","REJECTED","CANCELED","SUBMITTED"]},{"type":"REFUND","statuses":["CONFIRMED"]},{"type":"REWARD","statuses":["PENDING","CONFIRMED"]},{"type":"REWARD_WITHDRAWAL_ACH","statuses":["PENDING","CONFIRMED","REJECTED","SUBMITTED"]},{"type":"REWARD_WITHDRAWAL_CHECK","statuses":["SCHEDULED","PENDING","CONFIRMED","REJECTED","CANCELED","SUBMITTED"]},{"type":"FEE","statuses":["CONFIRMED"]},{"type":"INTEREST","statuses":["CONFIRMED"]},{"type":"CREDIT","statuses":["CONFIRMED"]},{"type":"PAYMENT_CHECK","statuses":["CONFIRMED","REJECTED"]}],"accrualTypesAndStatuses":[{"type":"ONE_TIME","statuses":["CONFIRMED"]},{"type":"SIGNUP","statuses":["CONFIRMED"]},{"type":"OFFER","statuses":["CONFIRMED"]}]},"pagination":{"limit":20,"lastID":"","nextToken":null}}'

response = requests.post("https://api.imprint.co/v1/activity/fetch", headers=headers, data=post_data, timeout=10)
data = response.json()

# Dump transactions JSON for debugging
# with open("transactions.json", mode="w", encoding="utf-8") as f:
#     json.dump(data, f, ensure_ascii=False, indent=4)

# Prepare CSV file
with open("transactions.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Payee", "Memo", "Outflow", "Inflow"])

    # Loop through transactions and write them to the CSV, see example-transactions.json for structure
    for transaction in data["activity"]:
        date = transaction["dateTime"].split(",")[0]
        payee = transaction["header"]

        memo = ""
        if "details" in transaction and "other" in transaction["details"]:
            memo += f"{transaction['details']['other']['category']} "
        memo += f"({transaction["transactionUUID"]})"

        amount = transaction['amount']['displayValue']

        is_negative = transaction["type"] == "OFFER" or transaction["amount"].get("negative", False)

        outflow = amount if not is_negative else "0"
        inflow = amount if is_negative else "0"

        logging.info(
            f"Date: {date} Out: {outflow:<7} In: {inflow:<7} Type: {transaction["type"]} Payee: {payee} Memo: {memo}"
        )
        writer.writerow([date, payee, memo, outflow, inflow])

print("CSV file generated successfully.")
