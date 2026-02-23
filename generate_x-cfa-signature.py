import jwt
import time

# The 15-character key you extracted via Frida
SIGNATURE_KEY = "redacted"

def generate_signature_header(secret_key):
    now = int(time.time())
        
    payload = {
        "iat": now,
        "nbf": now - 43200,
        "exp": now + 43200,
        "platform": "android",
        "build": "2026.3.0",
        "versionCode": "20260300",
        "serialNumber": "",
        # This is the FCM (Firebase Cloud Messaging) token from the network capture. 
        # Using a static one is usually fine unless they cross-reference push tokens aggressively.
        "pushRegistrationId": "redacted",
        "buildProfile": "appstore",
        "timezone": "America/New_York"
    }
    
    # Sign the token using HS512
    token = jwt.encode(payload, secret_key, algorithm="HS512")
    return token

if __name__ == "__main__":
    fresh_signature = generate_signature_header(SIGNATURE_KEY)
    print(f"Generated x-cfa-signature:\n{fresh_signature}")
