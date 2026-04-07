import os

GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
GMAIL_USER = os.getenv("GMAIL_USER")
SHEETS_URL = os.getenv("SHEETS_URL")

# API endpoints
TOKEN_URL = "https://login.my.chick-fil-a.com/as/token.oauth2"
LOYALTY_URL = "https://d2c.api.my.chick-fil-a.com/cfa.d2c.frontend.loyalty.v1.LoyaltyService/GetLoyaltySummary"

# HS512 private keys used to generate JSON Web Tokens to simulate
# a mobile operating system sending legitimate location headers.
# Captured from the mobile app using a Frida hook.
LOCATION_HS512 = os.getenv("LOCATION_HS512")
SIGNATURE_HS512 = os.getenv("SIGNATURE_HS512")

# Target coordinates to check for regional rewards in
# This is a list, but I HIGHLY RECOMMEND NOT PUTTING MULTIPLE SETS HERE
# unless you're trying to get your account banned.
# Format: list of lists, ["Location Label", latitudeDecimalDegrees, longitudeDecimalDegrees]
TARGET_COORDS = [
    #["Greater Triangle Area (Raleigh/Durham/Chapel Hill)", 35.7904, -78.6586]
    ["Northern California", 38.575764, -121.478851]
]

# OAuth2 tokens, captured from intercepted network requests
# Note that these are cross referenced with CLIENT_ID
# Mobile app tokens will not work with web app requests and vice versa
OAUTH_BASIC = os.getenv("OAUTH_BASIC")
OAUTH_REFRESH_TOKEN = os.getenv("OAUTH_REFRESH_TOKEN")

USER_AGENT = "v2026.3.0, Android 16"

# This is the FCM (Firebase Cloud Messaging) token from the capture. 
# Using a static one is usually fine unless they cross-reference push tokens aggressively.
# This does not change with different accounts as of writing.
PUSH_REGISTRATION_ID = os.getenv("PUSH_REGISTRATION_ID")

# This is either MobileV2 for mobile tokens, or PWO for web app tokens
CLIENT_ID = "PWO"

# The following are used to generate the signature header by mimicking an Android device
# You probably don't need to change any of this
PLATFORM = "android"
BUILD = "2026.3.0"
VERSION_CODE = "20260300"
SERIAL_NUMBER = ""
BUILD_PROFILE = "appstore"
TIMEZONE = "America/New_York"

# Maps protobuf output to fields, basically just adds labels
FIELD_MAP = {
    "1": "offers",
    "2": "currentPoints",
    "9": "customerId"
}
STATUS_MAP = {
    1: "active",
    2: "redeemed",
    3: "expired"
}
OFFER_MAP = {
    "1": "awardId",
    "2": "itemCategories",
    "3": "offerTemplateId",
    "4": "offerName",
    "5": "display",
    "6": "offerType",
    "7": "promotionId",
    "8": "status",
    "9": "subTitle",
    "10": "title",
    "14": "expiresOnDate",
    "15": "redeemedDate"
}
