import requests
import http.client
from bs4 import BeautifulSoup

imprint_access_token = "" # Extract from activity API call using browser dev tools
imprint_device_id = "" # Extract from activity API call using browser dev tools
imprint_signature = "" # Extract from activity API call using browser dev tools

# Enable HTTP debug logging
http.client.HTTPConnection.debuglevel = 1

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

# The rest of the script for building the OFX file remains the same
# Start building the OFX file
soup = BeautifulSoup(features="xml")
ofx = soup.new_tag("OFX")
soup.append(ofx)

bankmsgsrsv1 = soup.new_tag("BANKMSGSRSV1")
ofx.append(bankmsgsrsv1)

stmttrnrs = soup.new_tag("STMTTRNRS")
bankmsgsrsv1.append(stmttrnrs)

banktranlist = soup.new_tag("BANKTRANLIST")
stmttrnrs.append(banktranlist)

# Loop through transactions and add them to the OFX file
for transaction in data["activity"]:
    if transaction["type"] == "TRANSACTION":
        stmttrn = soup.new_tag("STMTTRN")
        banktranlist.append(stmttrn)

        trntype = soup.new_tag("TRNTYPE")
        trntype.string = "DEBIT" if transaction["amount"]["negative"] else "CREDIT"
        stmttrn.append(trntype)

        dtposted = soup.new_tag("DTPOSTED")
        dtposted.string = transaction["dateTime"].replace("/", "").replace(",", "").replace(" ", "").replace(":", "")
        stmttrn.append(dtposted)

        trnamt = soup.new_tag("TRNAMT")
        trnamt.string = str(transaction["amount"]["displayValue"])
        stmttrn.append(trnamt)

        fitid = soup.new_tag("FITID")
        fitid.string = transaction["id"]
        stmttrn.append(fitid)

        name = soup.new_tag("NAME")
        name.string = transaction["header"]
        stmttrn.append(name)

# Save the OFX file
with open("transactions.ofx", "w") as file:
    file.write(str(soup.prettify()))

print("OFX file generated successfully.")
