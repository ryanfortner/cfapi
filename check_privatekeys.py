import jwt

# The keys you extracted via Frida
KEY_A = ""
KEY_B = ""

x_cfa_location_token = ""
x_cfa_signature_token = ""

def test_key(token, token_name):
    print(f"Testing keys for {token_name}...")
    for key_name, key_val in [("Key A (128-char)", KEY_A), ("Key B (15-char)", KEY_B)]:
        try:
            # We use options={"verify_exp": False} because your captured token is expired
            decoded = jwt.decode(token, key_val, algorithms=["HS512"], options={"verify_exp": False})
            print(f"  [SUCCESS] {key_name} signed the {token_name} header!")
            print(f"  Payload: {decoded}\n")
            return key_val
        except jwt.InvalidSignatureError:
            print(f"  [FAILED] {key_name} is invalid for this token.")

test_key(x_cfa_location_token, "x-cfa-location")
test_key(x_cfa_signature_token, "x-cfa-signature")