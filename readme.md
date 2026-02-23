# cfapi

Reverse-engineering the Chick-fil-A rewards system.

Note: much of this is redacted (albeit pretty poorly). Anything that's redacted but not mentioned is not important from the context of this writeup.

## Why?

I like free food, probably more so than most other people, so much so that in my free time I find ways to get more free food. Not the best for my health, but if it’s free, you have to like it, right? 

Unlike most fast food restaurants, Chick-fil-A’s reward system is simple in the sense that all the “rewards” they give out are simple freebies. Not discounted items or BOGO deals, just **free items**. Their point system is similar to other restaurants, with a mediocre point conversion at best, but that’s besides the point. Having taken advantage of these free items in past years, I wanted an automated system to check for and claim any free rewards from sports games in my area or national promotional offers.

## Background Information

Most Chick-fil-A rewards come in the form of regional (“market”) offers. Something in their mobile app registers your GPS location, compares it in some geofencing algorithm, and checks for an offer in a specific market. While conceptually it’s pretty easy to understand, there is barely any information I could find on how this actually works on a lower level (and obviously they have no public API). So I recruited one of our friendly LLMs to do some deep research on how it actually works.

The fundamental unit of a reward in Chick-fil-A’s system is called a Digital Offer Card (DOC). You may have seen or used an actual Offer Card (they say “Be Our Guest” on the front, typically), these are just the digital versions of those. Restaurant owners/operators can digitally push these to customers, and apparently there’s considerable autonomy on that front. Additionally, operators can pool rewards, such as all operators from the Atlanta area for example, and run market-wide regional rewards. Important to note that the offer cards are paid for by the operators - they’re not just coupons, and it does result in a loss.

Something else I found interesting is that *allegedly* each restaurant has a Kubernetes cluster running on three small Intel NUC computers in a cabinet, which handle immediate processing of orders, and sync back to the cloud when connection is stable (thus allowing transactions even when the Internet is down). They call that Cloud-fil-A. I’m not doing research on this, but just thought it was kind of interesting.

## API Exploration

So, once again this is my first attempt at reverse engineering anything at all. I know that Chick-fil-A has some sort of API that checks for geolocated rewards as soon as you open the app. I also knew from prior knowledge (from being hardware banned from the app at one point) that their security policy is no joke, and they take zero chances when it comes to users signing up and claiming these rewards. They will not hesitate to shadow ban accounts at any moment. 

My initial approach was to use an Android emulator to sign in, while capturing requests through a man-in-the-middle proxy. That was a bit of a hassle to set up, but I got it working… after I managed to get my public IP banned from logging in. Like I said… no joke security policy, too many failed sign-ins and they’ll just ban the IP.

### token.oauth2 API Request

This is pretty much the “key” to using other parts of their API, namely any subdomain *.api.my.chick-fil-a.com. Note the difference between the two access token requests: the browser one uses `PWO` as its client ID, and the mobile one uses `MobileAppV2`. It's highly important that you **generate a mobile app token** if you want to view and claim rewards like a native app would.

#### Browser

Since I had access to a different computer (web-browser only) on a different public IP, I decided to try capturing network requests through the browser-based login page, hopefully being able to observe how their authorization process works, if nothing else. I know that they don’t issue location-based rewards through the website, but if I could get the authorization part complete, that would be spectacular.

It worked… so after capturing `refresh_token` and `client_secret` (all of which could be found within the POST request itself), I could execute the following command to get a working access token:

Of course, replacing REFRESH_TOKEN_HERE, and CLIENT_SECRET_HERE.

```shell
curl -X POST "https://login.my.chick-fil-a.com/as/token.oauth2" \
     -H "Host: login.my.chick-fil-a.com" \
     -H "User-Agent: redacted" \
     -H "Accept: application/json" \
     -H "Origin: https://order.chick-fil-a.com" \
     -H "Referer: https://order.chick-fil-a.com/" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     --data-urlencode "grant_type=refresh_token" \
     --data-urlencode "client_id=PWO" \
     --data-urlencode "refresh_token=REFRESH_TOKEN_HERE" \
     --data-urlencode "client_secret=CLIENT_SECRET_HERE"
```

This returns the following:

```json
{
  "access_token": "MY_ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 2399
}
```

Bingo! They do expire in about 40 minutes though. I’ll work fast (or generate another one 🙂). 

#### Mobile App

Generating mobile app tokens differs slightly in headers (namely the user agent and added `x-cfa-signature` [scroll down to the "Extracting Private Keys" section to see how this works]).

```shell
curl -X POST 'https://login.my.chick-fil-a.com/as/token.oauth2' \
  --http2 \
  --compressed \
  -H 'authorization: Basic OAUTH_BASIC_TOKEN_HERE' \
  -H 'x-cfa-signature: CFA_SIGNATURE_HERE' \
  -H 'user-agent: v2026.3.0, Android 16' \
  -H 'content-type: application/x-www-form-urlencoded' \
  -H 'x-datadog-sampling-priority: 0' \
  -d 'refresh_token=REFRESH_TOKEN_HERE&grant_type=refresh_token&client_id=MobileAppV2&realm=%2Fexternal'
```

The returned headers are exactly the same as authentication requests through a web browser, but the `access_token` is client-specific.


### PredictRestaurant API Request

d2c.api.my.chick-fil-a.com: likely stands for Direct to Customer. I observed a GET request that would “predict” which restaurant was closest to the user based on base64-encoded GPS coordinates.

```shell
curl -v -X GET "https://d2c.api.my.chick-fil-a.com/cfa.d2c.frontend.restaurant.v1.RestaurantService/PredictRestaurant?base64=1&connect=v1&encoding=proto&message=LOCATION_ENCODED" \
     -H "Authorization: Bearer MY_ACCESS_TOKEN" \
     -H "User-Agent: redacted" \
     -H "Origin: https://order.chick-fil-a.com" \
     -H "Referer: https://order.chick-fil-a.com/"
```

Note the `LOCATION_ENCODED` parameter in the URL of the request. This is the most important bit of information that we have to send to their API. I wasn’t sure exactly how they had encoded the coordinates, so I set the fake GPS location of the Android emulator to some coordinates in Austin, TX, and cross-referenced them to the argument in the API request that the app sent in order to successfully reverse-engineer the encoding method.

In the original `PredictRestaurant` request captured through the Android emulator and proxy, the URL contains the parameter `message=DTkj8kEVd3zDwhgCIAE=`. When the API processes this, it returns the store details for the “6th & Congress In-Line” location in Austin - success! So we can proceed with our mathematical analysis. I made extensive use of LLM technology to expand my knowledge on these decryption methods so that I could learn the terminology and conceptually understand what was being done, but I did not let it do all of the work for me.

Under the hood, there are two steps that Chick-fil-A engineers chose to send coordinate data. The first step, Protocol Buffer Serialization, “packs” the data using Google’s Protocol Buffers (protobufs). Before the data is sent, it is structured to a developer-provided schema, yielding a binary format. However, that can’t easily be put into a URL (it would be far too long with foreign characters), so the protobuf is Base64 encoded so that it’s printable in a URL (the second step). So let’s decode the Base64 string first.

#### Decoding Location Strings

Protobuf Wire Types (future reference for protobuf deserialization):
- 0: Varint, used for encoding integers, booleans, enums
- 1: 64-bit, used for fixed-length 64-bit datatypes such as double or fixed64
- 2: Length-delimited, used for strings, byte arrays
- 3,4: Groups (deprecated, haven’t read on this yet)
- 5: 32-bit, used for fixed-length 32-bit datatypes such as float or fixed32

1. Converting to Hexadecimal: Decoding `DTkj8kEVd3zDwhgCIAE=` yields 14 bytes of raw binary data. Represented in hexadecimal: 

    `0D 39 23 F2 41 15 77 7C C3 C2 18 02 20 01`

2. Protobuf Serialization: This is quite the task. Here goes.

    a. `0D`: Field 1 Tag
    
    Convert to binary: `0000 1101`. The last three bits show us that this is Wire Type 5, a 32-bit datatype. Bits are shifted right by three. 

    The remaining number is 1, telling the parser that, since it’s looking for four bytes (32-bits is 4 bytes) for Field 1.

    b. `39 23 F2 41`: Field 1 

    This is the next 4 bytes previously mentioned. Protobuf transmits numbers in little endian format, so we need to reverse order: `41 F2 23 39`

    We can now literally translate this into a standard floating-point decimal (IEEE 754 translation) -> `30.267199` - the latitude of Austin!

    c. `15`: Field 2 Tag
    
    Binary: `0001 0101`
    
    Last 3 bits: `101` = 5, we’re looking at a 32-bit again
    
    Remaining bits: `0001 0` = 2, looking like the value for Field 2 is again a 32-bit fixed datatype.

    d. `77 7C C3 C2`: Field 2
    
    Little-Endian conversion: `C2 C3 7C 77`
    
    IEEE 754 translation: `-97.743095` (longitude of Austin - bang!)

    e. `18`: Field 3 Tag
    
    Binary: `0001 1000`

    Last 3 bits: `000` = 0, Field 3 is a varint (variable integer), meaning it could be any number of bytes long, depending on how large the number is.

    In order to know how long a varint is, we look at the first bit of the byte. If 1, we continue, if it’s 0, we read it as the last bit of the number.

    f. `02`: Field 3
    
    Binary: `0000 0010`
    
    The first bit is 0, so we stop here. The value is 2. 

    g. `20`: Field 4 Tag
	
    Binary: `0010 0000`
	
    Another varint

    h. `01`: Field 4
    
    Binary: `0000 0001`
    
    First bit zero, we stop here. The value is 1.

After all of that, we arrive at the following:

    Field 1: 30.267199
    Field 2: -97.743095
    Field 3: 2
    Field 4: 1

I’m still not sure what Field 3 and 4 are, but I keep those the same in subsequent API calls, just so I have the best chance of replicating the request accurately. 

#### Encoding Location Strings

At this point I now know how exactly location strings are transmitted, so let's whip up a Python script to do the reencrypting for us.

```python
import struct
import base64

# Set target GPS coordinates
lat = 30.267199
lon = -97.743095

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
```

Now we’re ready to make our request. I logged CURL’s output to an arbitrary file, in which I could confirm I got a huge string of data (something like HTML) with the data of that one Austin, TX restaurant I mentioned earlier. So the geolocation request did indeed work. Here’s CURL’s raw output (with some things removed so it’s not so long):

```html
* Connected to d2c.api.my.chick-fil-a.com (172.64.153.189) port 443
* Server certificate:
*  subject: CN=d2c.api.my.chick-fil-a.com
*  start date: redacted 2026 GMT
*  expire date: redacted 2026 GMT
< HTTP/2 200 
< date: redacted 2026 GMT
< content-type: application/proto
< server: cloudflare
< cf-ray: redacted
< cf-cache-status: DYNAMIC
< accept-encoding: gzip
< access-control-allow-origin: https://order.chick-fil-a.com
< cache-control: max-age=120
< strict-transport-security: max-age=0
< vary: Origin,Accept-Encoding
< access-control-allow-credentials: true
< x-envoy-upstream-service-time: 148
< set-cookie: __cf_bm=CFBMCOOKIE; path=/; expires=redacted; domain=.my.chick-fil-a.com; HttpOnly; Secure; SameSite=None
< set-cookie: _cfuvid=CFUVIDCOOKIE; path=/; domain=.my.chick-fil-a.com; HttpOnly; Secure; SameSite=None
```

Almost done here… it’s a lot, yeah, I’m aware. There are two things we need at this point: notice how the request sends us cookies? `__cf_bm`, which is Cloudflare bot management, and `_cfuvid`, a rate limiting cookie, also from Cloudflare. We need to save these for subsequent requests. Or, use a Python Session.

### GetLoyaltySummary API Request

This basically returns our entire inventory so that I can check whether or not a regional reward was actually received.

#### Just Checking

This will not pass a location in with the API request. This type should only be done with a **browser access_token**, not mobile.

```shell
curl -X POST "https://commerce.api.my.chick-fil-a.com/cfa.d2c.frontend.loyalty.v1.LoyaltyService/GetLoyaltySummary" \
     -H "Authorization: Bearer MY_ACCESS_TOKEN" \
     -H "Cookie: _cfuvid=CFUVIDCOOKIE; __cf_bm=CFBMCOOKIE" \
     -H "Content-Type: application/json" \
     -H "User-Agent: redacted" \
     -H "Origin: https://www.chick-fil-a.com" \
     -H "Referer: https://www.chick-fil-a.com/" \
     -d "{}"
```

The returned data:

```json
{
  "offers": [
    {
      "awardId": "redacted",
      "itemCategories": [
        {
          "name": "Chick-fil-A® Chicken Biscuit",
          "imageUri": "https://www.cfacdn.com/img/order/menu/Mobile/Breakfast/Menu%20Item/Edited_400x280/ChickenBiscuit_mobile.webp",
          "itemTags": [
            "BISCUIT_CHICKEN",
            "STC_BISCUIT_CHICKEN"
          ]
        }
      ],
      "offerTemplateId": "redacted",
      "offerName": "Chick-fil-A® Chicken Biscuit",
      "display": {
        "templateType": "corporate",
        "templateSubType": "bonus"
      },
      "offerType": "nationalGiveaway",
      "promotionId": "NATIONAL_GIVEAWAY_PROMOTION_FEB_2026",
      "status": "PROMO_OFFER_STATUS_AVAILABLE",
      "subTitle": "Thanks for being a Chick-fil-A One Member. We can't wait to serve you soon.",
      "title": "Enjoy breakfast on us",
      "expiresOnDate": {
        "year": 2026,
        "month": 2,
        "day": 28
      }
    }
  ],
  "pointsToReachNextTier": 1000,
  "currentTier": {},
  "tierList": [],
  "customerId": "CFAID-redacted"
}
```

#### Checking & Claiming

This should only be done with a **mobile API key**, and passed in with a properly encrypted `x-cfa-location` header AND `x-cfa-signature`. Once again, see "Extracting Private Keys". I can't help with that part.

```shell
curl -X POST "https://d2c.api.my.chick-fil-a.com/cfa.d2c.frontend.loyalty.v1.LoyaltyService/GetLoyaltySummary" \
     --http2 \
     --compressed \
     -H "connect-protocol-version: 1" \
     -H "x-cfa-location: CFA_LOCATION" \
     -H "connect-timeout-ms: 10000" \
     -H "x-cfa-signature: CFA_SIGNATURE" \
     -H "user-agent: v2026.3.0, Android 16" \
     -H "authorization: Bearer MY_ACCESS_TOKEN" \
     -H "content-type: application/proto" \
     -H "x-datadog-sampling-priority: 0" \
     --data-binary $'\x00\x00\x00\x00' | protoc --decode_raw
```

This returns the same exact thing as the "Just Checking" request, except with applicable regional offers **pre-claimed**, which is neat.

## Extracting Private Keys

When `x-cfa-location` and `x-cfa-signature` are sent to the server through an API request, they are not in plaintext. They are encrypted JSON web tokens (JWT) that use a private key. My goal was to create requests that mimic a genuine mobile operating system, so I'd have to create fake JWTs to pass to the API, meaning I'd also have to have access to the private keys in question.

As suggested after much research, I captured the HS512 keys through a Frida script (see `findkeys-frida.js`). This produced two different keys. I did't know which one signed which header, so I used a script `check_privatekeys.py`, generated by artificial intelligence to tell me exactly which key signed which header.

I then threw together two header generation scripts (`generate_x-cfa-location.py`, `generate_x-cfa-signature.py`).

Reproducing these keys on public sites opens up a legal box that I have no desire to open.

## Writing & Testing a Script

Here's an example of me testing `claim_check.py`. It assembles a chain of requests, handling all encoding/decoding for me.

![claimcheck](claimcheck.png)

## App Data Collection

This section aims to highlight something I encountered while capturing network requests. Chick-fil-A collects an absurd amount of data through their app, like so much data that I thought I was analyzing my banking app by accident. We’re talking EVERY metric an Android app is even allowed to access. Screen size (pixel density???), serial number, how the app was installed, even widgets. Is that really necessary for a fast-food app? Even for security reasons, I think not…

I briefly considered reproducing said metrics here but, a. the list would be insanely long and b. I don't want to go through the redaction trouble.

## References

Thanks to these sites that helped me understand how to RE this stuff.

- https://www.jwt.io/
- https://www.h-schmidt.net/FloatConverter/IEEE754.html
- https://victoriametrics.com/blog/go-protobuf/
- https://www.biaodianfu.com/google-protocol-buffers.html
