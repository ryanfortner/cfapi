import struct
import base64

# Set target GPS coordinates
lat = 0.0
lon = 0.0

# Set the default parameters as observed in the API traffic
field3 = 2
field4 = 1

# Pack the floats into 4-byte Little-Endian binary strings ('<f')
lat_bytes = struct.pack('<f', lat)
lon_bytes = struct.pack('<f', lon)

# Pack the integer flags (since they are under 128, we can just use raw bytes)
field3_bytes = bytes([field3])
field4_bytes = bytes([field4])

# Concatenate tags and values into a single binary stream
# 0x0D -> Field 1 (Lat), Wire Type 5 (32-bit float)
# 0x15 -> Field 2 (Lon), Wire Type 5 (32-bit float)
# 0x18 -> Field 3 Wire Type 0 (Varint)
# 0x20 -> Field 4 Wire Type 0 (Varint)
raw_protobuf_stream = (
    b'\x0d' + lat_bytes +
    b'\x15' + lon_bytes +
    b'\x18' + field3_bytes +
    b'\x20' + field4_bytes
)

# Encode the raw binary stream to Base64
encoded_b64 = base64.b64encode(raw_protobuf_stream).decode('utf-8')

# Output result
print(encoded_b64)

