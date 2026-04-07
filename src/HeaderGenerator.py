import jwt
import time
from Constants import *

def generate_location_header(lat, long):
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

    token = jwt.encode(payload, LOCATION_HS512, algorithm="HS512")
    print("Location Header:")
    print(token)
    return token

def generate_signature_header():
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
        "platform": PLATFORM,
        "build": BUILD,
        "versionCode": VERSION_CODE,
        "serialNumber": SERIAL_NUMBER,
        "pushRegistrationId": PUSH_REGISTRATION_ID,
        "buildProfile": BUILD_PROFILE,
        "timezone": TIMEZONE
    }
    
    # Sign the token using HS512
    token = jwt.encode(payload, SIGNATURE_HS512, algorithm="HS512")
    print("Signature Header:")
    print(token)
    return token