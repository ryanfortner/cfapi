# Checks for and claims regional rewards
# Danger - you might get your account banned.

import time
import json
import jwt
import requests
import blackboxprotobuf

# KEYS
LOCATION_HS512 = ""
SIGNATURE_HS512 = ""

# CONFIGURATION
TARGET_LATITUDE = 0.0
TARGET_LONGITUDE = 0.0
OAUTH_BASIC = ""
OAUTH_REFRESH_TOKEN = ""
USER_AGENT = ""

def generate_location_header(lat, long, location_key):
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
    now = int(time.time())
        
    payload = {
        "iat": now,
        "nbf": now - 43200,
        "exp": now + 43200,
        "platform": "android",
        "build": "2026.3.0",
        "versionCode": "20260300",
        "serialNumber": "",
        "pushRegistrationId": "redacted",
        "buildProfile": "appstore",
        "timezone": "America/New_York"
    }
    
    token = jwt.encode(payload, signature_key, algorithm="HS512")
    return token

def decode_grpc_web_response(binary_data):
    """
    Decodes pure Protobuf data. No gRPC envelope stripping required
    for Connect Unary requests (application/proto).
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

def print_rewards(cleaned_data):
    """
    Parses the cleaned dictionary to print a readable list of rewards.
    Assumes Field '1' is the list of rewards.
    """
    print("\n" + "="*40)
    print("       AVAILABLE REGIONAL REWARDS")
    print("="*40)

    # Field "1" typically contains the list of reward objects
    rewards = cleaned_data.get("1", [])
    
    if not rewards:
        print("No rewards found in response.")
        return

    count = 0
    for reward in rewards:
        # Field mapping based on observation:
        # "10": Title / Short Promo Text
        # "4":  Item Name
        # "9":  Description / Detail
        # "14": Expiration Date Object {1: Year, 2: Month, 3: Day}
        
        title = reward.get("10", "Unknown Title")
        item_name = reward.get("4", "Unknown Item")
        description = reward.get("9", "")
        
        # Parse Expiry Date
        expiry_obj = reward.get("14", {})
        expiry_str = "N/A"
        if expiry_obj:
            y = expiry_obj.get("1")
            m = expiry_obj.get("2")
            d = expiry_obj.get("3")
            if y and m and d:
                expiry_str = f"{m}/{d}/{y}"

        print(f"\nOFFER #{count + 1}: {title}")
        print(f"Item:       {item_name}")
        print(f"Details:    {description}")
        print(f"Expires:    {expiry_str}")
        print("-" * 40)
        count += 1
    
    print(f"\nTotal Rewards Found: {count}")

def main():
    # Handles cookies automatically
    session = requests.Session()

    # Generate headers
    signature = generate_signature_header(SIGNATURE_HS512)
    location = generate_location_header(TARGET_LATITUDE, TARGET_LONGITUDE, LOCATION_HS512)

    # Refresh access token
    print("Refreshing access token...")

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
        print(f"Failed to refresh token: {token_response.status_code}")
        print(token_response.text)
        return
    
    access_token = token_response.json().get("access_token")
    print("Access token obtained.")

    # Print loyalty summary
    print("Obtaining loyalty summary...")

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
        print("Success! Decoding received response...")
        
        # Decode raw protobuf
        decoded_data = decode_grpc_web_response(response.content)

        # Clean bytes to strings
        cleaned_data = clean_protobuf_data(decoded_data)

        # Print cleaned data, for visualization purposes
        print(json.dumps(cleaned_data, indent=4))

        # Print formatted output
        print_rewards(cleaned_data)

    else:
        print(f"Request failed with status: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()