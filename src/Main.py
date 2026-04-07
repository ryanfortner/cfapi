import json
import requests
import warnings
import os
import HeaderGenerator
import ProtobufDecode
import FormatData
import Notifier
import time
import sys

from jwt import InsecureKeyLengthWarning
from Constants import *
from datetime import datetime, timezone

def main():
    # Ignore keys that are "too short"
    warnings.filterwarnings("ignore", category=InsecureKeyLengthWarning)

    # Handles cookies automatically
    session = requests.Session()

    response = None

    for coords in TARGET_COORDS:

        print(f"[*] Checking ({coords[1]}, {coords[2]}), {coords[0]}")

        # Generate appropriate headers for this location
        signature = HeaderGenerator.generate_signature_header()
        location = HeaderGenerator.generate_location_header(coords[1], coords[2])
        
        token_headers = {
            "authorization": f"Basic {OAUTH_BASIC}",
            "x-cfa-signature": signature,
            "user-agent": USER_AGENT,
            "content-type": "application/x-www-form-urlencoded"
        }

        token_data = {
            "refresh_token": OAUTH_REFRESH_TOKEN,
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "realm": "/external"
        }

        token_response = session.post(TOKEN_URL, headers=token_headers, data=token_data)

        if (token_response.status_code != 200):
            print(f"[!] Failed to refresh token: {token_response.status_code}")
            print(token_response.text)
            return
        
        access_token = token_response.json().get("access_token")
        
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

        response = session.post(LOYALTY_URL, headers=loyalty_headers, data=proto_payload)

    if response.status_code == 200:
        print("[*] Decoding received response...")
        
        # Decode raw protobuf
        decoded_data = ProtobufDecode.decode_protobuf(response.content)

        # Clean bytes to strings
        cleaned_data = ProtobufDecode.clean_protobuf_data(decoded_data)

        # Format dictionary
        geodata = FormatData.extract_public_geos(cleaned_data)

        epoch_time = int(time.time())

        compiled_filepath = "../output/geodata-latest.json"
        
        # Safely get the offers list
        current_offers = geodata.get('offers', []) if isinstance(geodata, dict) else []
        compiled_offers_dict = {}
        
        # Load existing data to preserve timestamps
        if os.path.exists(compiled_filepath):
            try:
                with open(compiled_filepath, 'r') as f:
                    compiled_data = json.load(f)
                    for offer in compiled_data.get('offers', []):
                        if 'promotionId' in offer:
                            compiled_offers_dict[offer['promotionId']] = offer
            except Exception as e:
                print(f"[!] Warning: Could not read existing {compiled_filepath}: {e}")
                
        # Build the updated list
        updated_offers = []
        for offer in current_offers:
            promo_id = offer.get('promotionId')
            if promo_id and promo_id in compiled_offers_dict:
                # Keep existing timestamp if we've seen this before
                offer['timestamp'] = compiled_offers_dict[promo_id].get('timestamp', epoch_time)
            else:
                # Mark as newly seen
                offer['timestamp'] = epoch_time

                offer_name = offer.get('offerName', 'New Special Reward')
                
                # Format a quick expiration string for the email
                exp = offer.get('expiresOnDate', {})
                exp_text = f"{exp.get('year')}-{str(exp.get('month')).zfill(2)}-{str(exp.get('day')).zfill(2)}"
                
                # Call the Notifier
                print(f"[*] New offer detected: {offer_name}. Triggering alerts...")
                Notifier.send_alerts(offer_name, exp_text)
                
            updated_offers.append(offer)
            
        # Reconstruct geodata to maintain any other top-level keys
        if isinstance(geodata, dict):
            geodata['offers'] = updated_offers
        else:
            geodata = {"offers": updated_offers}

        print(f"[*] Writing updated geodata API output to {compiled_filepath}")
        with open(compiled_filepath, "w") as json_file:
            json.dump(geodata, json_file, indent=4)

    else:
        print(f"[!] Request failed with status: {response.status_code}")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
