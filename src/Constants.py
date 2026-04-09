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
    # Core & High-Density Markets
    ["Atlanta, GA (Corporate HQ)", 33.7490, -84.3880],
    ["Dallas-Fort Worth, TX", 32.7767, -96.7970],
    ["Houston, TX", 29.7604, -95.3698],
    ["San Antonio, TX", 29.4241, -98.4936],
    ["Austin, TX", 30.2672, -97.7431],
    ["Los Angeles, CA (SoCal Co-op)", 34.0522, -118.2437],
    ["Washington, D.C. / Baltimore", 38.9072, -77.0369],
    ["Charlotte, NC", 35.2271, -80.8431],
    ["Raleigh-Durham, NC", 35.7796, -78.6382],
    
    # User-Requested Additions
    ["Northern California / Bay Area, CA", 37.7749, -122.4194],
    ["Sacramento, CA", 38.5816, -121.4944],
    ["Central Indiana / Indianapolis, IN", 39.7684, -86.1581],
    
    # Additional Major Active DMAs
    ["Orlando, FL", 28.5383, -81.3792],
    ["Tampa Bay, FL", 27.9506, -82.4572],
    ["Miami / South Florida", 25.7617, -80.1918],
    ["Chicago, IL", 41.8781, -87.6298],
    ["Phoenix, AZ", 33.4484, -112.0740],
    ["Nashville, TN", 36.1627, -86.7816],
    ["Denver, CO", 39.7392, -104.9903],
    ["Philadelphia, PA", 39.9526, -75.1652],
    ["New York Tri-State Area", 40.7128, -74.0060],
    ["Seattle / Pacific Northwest", 47.6062, -122.3321],
    ["Salt Lake City, UT", 40.7608, -111.8910],
    ["Kansas City, MO/KS", 39.0997, -94.5786],
    ["St. Louis, MO", 38.6270, -90.1994],
    ["Columbus, OH", 39.9612, -82.9988],
    ["Cincinnati, OH", 39.1031, -84.5120],
    ["Detroit, MI", 42.3314, -83.0458],
    ["Minneapolis-St. Paul, MN", 44.9778, -93.2650],
    ["Las Vegas, NV", 36.1699, -115.1398]
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

# This is either MobileAppV2 for mobile tokens, or PWO for web app tokens
CLIENT_ID = "MobileAppV2"

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
