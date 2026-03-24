import blackboxprotobuf

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