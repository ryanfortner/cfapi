import time
import json
import jwt
import requests
import blackboxprotobuf
import qrcode
import warnings
import os
import sys
from datetime import datetime
from jwt import InsecureKeyLengthWarning

# KEYS
LOCATION_HS512 = os.getenv("LOCATION_HS512")
SIGNATURE_HS512 = os.getenv("SIGNATURE_HS512")

# CONFIGURATION
TARGET_LATITUDE = 35.7721
TARGET_LONGITUDE = -78.6386
OAUTH_BASIC = os.getenv("OAUTH_BASIC")
OAUTH_REFRESH_TOKEN = os.getenv("OAUTH_REFRESH_TOKEN")
USER_AGENT = "v2026.3.0, Android 16"
# This is the FCM (Firebase Cloud Messaging) token from the capture. 
# Using a static one is usually fine unless they cross-reference push tokens aggressively.
PUSH_REGISTRATION_ID = os.getenv("PUSH_REGISTRATION_ID")

def generate_location_header(lat, long, location_key):
    """
    Generates x-cfa-location header using specified latitude/longitude coordinates
    in decimal degrees, and the private key from the app
    """

    now = int(time.time())

    payload = {
        "iat": now,
        "nbf": now - 300, 
        "exp": now + 300, 
        "lat": lat,
        "long": long,
        "horizontalAccuracyMeters": 5
    }

    token = jwt.encode(payload, location_key, algorithm="HS512")

    return token

def generate_signature_header(signature_key):
    """
    Generate x-cfa-signature header for verification of requests
    to spoof coming from an Android device
    """
    
    now = int(time.time())
    
    # 12 hours in seconds
    twelve_hours = 43200
    
    payload = {
        "iat": now,
        "nbf": now - twelve_hours,
        "exp": now + twelve_hours,
        "platform": "android",
        "build": "2026.3.0",
        "versionCode": "20260300",
        "serialNumber": "",
        "pushRegistrationId": PUSH_REGISTRATION_ID,
        "buildProfile": "appstore",
        "timezone": "America/New_York"
    }
    
    # Sign the token using HS512
    token = jwt.encode(payload, signature_key, algorithm="HS512")
    return token

def decode_protobuf(binary_data):
    """
    This decodes protobuf data received from requests
    that give us application/proto responses.
    """
    try:
        # If the response is truly empty, return an empty dict
        if not binary_data:
            return {"info": "Empty response body"}

        # Decode directly using blackboxprotobuf
        message_dict, typedef = blackboxprotobuf.decode_message(binary_data)
        return message_dict

    except Exception as e:
        return {
            "error": f"Failed to decode: {str(e)}", 
            "raw_hex": binary_data.hex()
        }

def clean_protobuf_data(data):
    """
    Recursively converts bytes to UTF-8 strings in a dictionary/list structure.
    """
    if isinstance(data, dict):
        return {k: clean_protobuf_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_protobuf_data(v) for v in data]
    elif isinstance(data, bytes):
        try:
            return data.decode('utf-8')
        except:
            return str(data)
    else:
        return data

def rewards_to_list(cleaned_data):
    """
    Convert cleaned rewards data into a list of dictionaries
    with important values already populated.
    """

    rewards = cleaned_data.get("1", [])
    
    if not rewards:
        print("\nNo rewards found in response.")
        return

    rewards_list = []

    for reward in rewards:
        status = reward.get("8") # 1 = Available, 2 = Redeemed
        title = reward.get("10", "No Title")
        item_name = reward.get("4", "Unknown Item")
        context = reward.get("9", "") # longer description/message

        offer_type = reward.get("5", {}).get("1", "unknown")
        scope = "National" if offer_type == "corporate" else "Local"
        
        ts_val = reward.get("15", {}).get("1") # Field 15: Precise Unix timestamp (present in redeemed items)
        date_obj = reward.get("14", {}) # Field 14: Structured date {1:Year, 2:Month, 3:Day} (present in unredeemed items)
        
        date_str = "Unknown Date"
        date_label = "Expires"

        if status == 2:
            # If redeemed, Field 15 is the redemption time
            if ts_val:
                dt = datetime.fromtimestamp(ts_val)
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                date_label = "Redeemed"
        else:
            # If unredeemed, Field 14 contains the Expiry Date
            y = date_obj.get("1")
            m = date_obj.get("2")
            d = date_obj.get("3")
            
            if y and m and d:
                # Format as MM/DD/YYYY
                date_str = f"{m}/{d}/{y}"
                date_label = "Expires"
            elif ts_val:
                # Fallback to timestamp if Field 14 is missing but 15 exists
                dt = datetime.fromtimestamp(ts_val)
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')

        reward_entry = {
            "title": title,
            "scope": scope,
            "item": item_name,
            "context": context,
            "date_label": date_label,
            "date_str": date_str
        }
        
        if status == 1:
            rewards_list.append(reward_entry)

    
    return rewards_list

def main():
    # Ignore keys that are "too short"
    warnings.filterwarnings("ignore", category=InsecureKeyLengthWarning)

    # Handles cookies automatically
    session = requests.Session()

    # Generate headers
    print("[*] Generating x-cfa-signature...")
    signature = generate_signature_header(SIGNATURE_HS512)
    print(f"[*] Generating x-cfa-location for {TARGET_LATITUDE, TARGET_LONGITUDE}")
    location = generate_location_header(TARGET_LATITUDE, TARGET_LONGITUDE, LOCATION_HS512)

    # Refresh access token
    print("[*] Refreshing access token...")

    token_url = "https://login.my.chick-fil-a.com/as/token.oauth2"

    token_headers = {
        "authorization": f"Basic {OAUTH_BASIC}",
        "x-cfa-signature": signature,
        "user-agent": USER_AGENT,
        "content-type": "application/x-www-form-urlencoded"
    }

    token_data = {
        "refresh_token": OAUTH_REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": "MobileAppV2",
        "realm": "/external"
    }

    token_response = session.post(token_url, headers=token_headers, data=token_data)

    if (token_response.status_code != 200):
        print(f"[!] Failed to refresh token: {token_response.status_code}")
        print(token_response.text)
        return
    
    access_token = token_response.json().get("access_token")

    # Print loyalty summary
    print("[*] Obtaining loyalty summary...")

    loyalty_url = "https://d2c.api.my.chick-fil-a.com/cfa.d2c.frontend.loyalty.v1.LoyaltyService/GetLoyaltySummary"
    
    loyalty_headers = {
        "connect-protocol-version": "1",
        "x-cfa-location": location,
        "connect-timeout-ms": "10000",
        "x-cfa-signature": signature,
        "user-agent": USER_AGENT,
        "authorization": f"Bearer {access_token}",
        "content-type": "application/proto",
        "x-datadog-sampling-priority": "0"
    }

    # This represents an empty Protobuf message (0 flags, 0 length)
    proto_payload = b''

    response = session.post(loyalty_url, headers=loyalty_headers, data=proto_payload)

    if response.status_code == 200:
        print("[*] Decoding received response...")
        
        # Decode raw protobuf
        decoded_data = decode_protobuf(response.content)

        # Clean bytes to strings
        cleaned_data = clean_protobuf_data(decoded_data)

        with open('data.json', 'w') as f:
            json.dump(rewards_to_list(cleaned_data), f)

        print("Data saved to data.json")

    else:
        print(f"[!] Request failed with status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
