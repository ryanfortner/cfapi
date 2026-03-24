import jwt
import time

LOCATION_KEY = "redacted"
LATITUDE = 0.0
LONGITUDE = 0.0

def generate_location_header(lat, lng, location_key):
    now = int(time.time())
    
    payload = {
        "iat": now,
        "nbf": now - 300, 
        "exp": now + 300, 
        "lat": lat,
        "long": lng,
        "horizontalAccuracyMeters": 5
    }
    
    token = jwt.encode(payload, location_key, algorithm="HS512")
    return token

if __name__ == "__main__":
    fresh_location = generate_location_header(LATITUDE, LONGITUDE, LOCATION_KEY)
    print(f"Generated x-cfa-location:\n{fresh_signature}")
