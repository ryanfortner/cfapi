from Constants import *
from datetime import datetime, timezone

def map_loyalty_data(raw_dict):
    """
    Maps numeric Protobuf keys to human-readable identifiers 
    based on the GetLoyaltySummary schema, handling structural variations.
    """

    # Map top level keys
    mapped_data = {FIELD_MAP.get(k, k): v for k, v in raw_dict.items()}

    # Map offers list
    if "offers" in mapped_data:
        cleaned_offers = []
        for offer in mapped_data["offers"]:
            cleaned_offer = {OFFER_MAP.get(str(k), k): v for k, v in offer.items()}
            
            # Display Mapping
            if "display" in cleaned_offer and isinstance(cleaned_offer["display"], dict):
                disp = cleaned_offer["display"]
                cleaned_offer["display"] = {
                    "templateType": disp.get("1", "spotlight"),
                    "templateSubType": disp.get("2", ""),
                    "message": disp.get("3", "")
                }

            # Map itemCategories (handling both dicts and lists)
            if "itemCategories" in cleaned_offer:
                item_cats = cleaned_offer["itemCategories"]
                # If it's a single dictionary, wrap it in a list so we can loop it reliably
                if isinstance(item_cats, dict):
                    item_cats = [item_cats]
                
                cleaned_cats = []
                for item in item_cats:
                    # Tags can be a single string or a list of strings
                    tags = item.get("3", [])
                    if not isinstance(tags, list):
                        tags = [tags]
                        
                    cleaned_cats.append({
                        "name": item.get("1"), 
                        "imageUri": item.get("2"), 
                        "itemTags": tags
                    })
                cleaned_offer["itemCategories"] = cleaned_cats
            
            # Map status integer to readable string
            if "status" in cleaned_offer:
                status_code = cleaned_offer["status"]
                # Uses .get() to return the string, or defaults back to the number if it's an unknown code
                cleaned_offer["status"] = STATUS_MAP.get(status_code, status_code)
            
            # Map expiresOnDate
            if "expiresOnDate" in cleaned_offer and isinstance(cleaned_offer["expiresOnDate"], dict):
                date = cleaned_offer["expiresOnDate"]
                cleaned_offer["expiresOnDate"] = {
                    "year": date.get("1"), 
                    "month": date.get("2"), 
                    "day": date.get("3")
                }

            # Map redeemedDate (Convert Unix timestamp to readable string)
            if "redeemedDate" in cleaned_offer and isinstance(cleaned_offer["redeemedDate"], dict):
                unix_time = cleaned_offer["redeemedDate"].get("1")
                if unix_time:
                    # Converts the integer (e.g., 1765468116) to a UTC datetime object
                    readable_date = datetime.fromtimestamp(unix_time, tz=timezone.utc)
                    # Formats it cleanly: "2025-12-11 15:48:36"
                    cleaned_offer["redeemedDate"] = readable_date.strftime('%Y-%m-%d %H:%M:%S')
                
            cleaned_offers.append(cleaned_offer)
        mapped_data["offers"] = cleaned_offers

    # 3. Map Tier List
    if "tierList" in mapped_data:
        cleaned_tiers = []
        for tier in mapped_data["tierList"]:
            cleaned_tiers.append({
                "id": tier.get("1"),
                "name": tier.get("2"),
                "startRange": tier.get("3"),
                "endRange": tier.get("4"),
                "multiplier": tier.get("5")
            })
        mapped_data["tierList"] = cleaned_tiers

    # 4. Map Current Tier Status
    if "currentTier" in mapped_data:
        ct = mapped_data["currentTier"]
        tier_info = ct.get("7") # Key 7 inside currentTier holds the tier definitions
        if tier_info:
            ct["tierInfo"] = {
                "id": tier_info.get("1"),
                "name": tier_info.get("2"),
                "startRange": tier_info.get("3"),
                "endRange": tier_info.get("4"),
                "multiplier": tier_info.get("5")
            }
            del ct["7"] # Clean up the old numeric key

    return mapped_data

def extract_public_geos(raw_dict):
    """
    Extracts only active geoGiveaway rewards and their non-sensitive metadata.
    Strips all PII, tier data, and non-relevant offers.
    """
    public_data = {"offers": []}
    
    # In the raw dict, "1" is the list of offers
    raw_offers = raw_dict.get("1", [])
    
    for offer in raw_offers:
        # Check if it's a geoGiveaway (Key "6")
        if offer.get("6") != "geoGiveaway":
            continue
            
        # Check if it's active (Key "8" == 1)
        # if offer.get("8") != 1:
        #     continue
            
        # If it passes the filters, extract only the safe fields
        safe_offer = {
            "offerName": offer.get("4"),
            "subTitle": offer.get("9"),
            "title": offer.get("10"),
            "promotionId": offer.get("7")
        }
        
        # 1. Extract itemCategories (Key "2") safely
        item_cats = offer.get("2")
        if item_cats:
            # Handle the single-dict vs list-of-dicts quirk
            if isinstance(item_cats, dict):
                item_cats = [item_cats]
                
            cleaned_cats = []
            for item in item_cats:
                tags = item.get("3", [])
                if not isinstance(tags, list):
                    tags = [tags]
                    
                cleaned_cats.append({
                    "name": item.get("1"),
                    "imageUri": item.get("2"),
                    "itemTags": tags
                })
            safe_offer["itemCategories"] = cleaned_cats
            
        # 2. Extract expiresOnDate (Key "14")
        expires_date = offer.get("14")
        if isinstance(expires_date, dict):
            safe_offer["expiresOnDate"] = {
                "year": expires_date.get("1"),
                "month": expires_date.get("2"),
                "day": expires_date.get("3")
            }
            
        public_data["offers"].append(safe_offer)
        
    return public_data
