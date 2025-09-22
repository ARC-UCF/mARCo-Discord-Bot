import requests
import re
import global_vars

globalRequestHeader = global_vars.globalRequestHeader

counties = global_vars.counties
marine_regions = global_vars.marine_regions

ZONE_MAP = {}

def build_zone_map(): # Build the map for zones.
    url = "https://api.weather.gov/zones?type=forecast&area=FL" # FLZ area, for most storm-based alerts.
    resp = requests.get(url, headers=globalRequestHeader)

    try:
        r = resp.json()
    except Exception as e:
        raise RuntimeError(f"Failed to parse JSON from NWS: {e}")

    if "features" not in r:
        raise RuntimeError(f"NWS API error: {r}")

    for feature in r["features"]:
        zone_id = feature["id"]
        name = feature["properties"]["name"]
        state = feature["properties"]["state"]
        ZONE_MAP[zone_id] = f"{name}, {state}"
    
    url_flood = "https://api.weather.gov/zones?type=county&area=FL" # FLC area, for floods.
    resp = requests.get(url_flood, headers=globalRequestHeader)
    r = resp.json()
    if "features" not in r:
        raise RuntimeError(f"NWS API error (flood zones): {r}")
    for feature in r["features"]:
        zone_id = feature["id"]
        name = feature["properties"]["name"]
        state = feature["properties"]["state"]
        ZONE_MAP[zone_id] = f"{name}, {state}"

def is_county_monitored(zones): # Checking if the alert includes the monitored counties.
    normalized_counties = [] # Normalize to account for any weird spelling variations that may occur.
    included = []
    print(zones)
    for c in counties:
        parts = c.lower().replace(" county", "").strip().split(",")
        county_name = parts[0].strip()
        county_state = parts[1].strip().upper() if len(parts) > 1 else ""
        normalized_counties.append((county_name, county_state))

    for z in zones: # Compare against zone map.
        if z in ZONE_MAP:
            zone_full = ZONE_MAP[z].replace(" county", "").strip()
            zone_parts = zone_full.split(",")
            zone_name_raw = zone_parts[0].lower().strip()
            zone_state = zone_parts[1].strip().upper() if len(zone_parts) > 1 else ""

            print(f"Checking zone {z} → {ZONE_MAP[z]} (normalized: name='{zone_name_raw}', state='{zone_state}')")

            # split zone_name_raw by comma, slash, 'and'
            zone_names = re.split(r',|/| and ', zone_name_raw)
            zone_names = [z.strip() for z in zone_names if z.strip()]

            for county_name, county_state in normalized_counties:
                if county_state == zone_state:
                    for zn in zone_names:
                        if county_name in zn:  # substring match
                            print(f"✅ Match found (substring): {ZONE_MAP[z]} includes {county_name}, {county_state}")
                            included.append(str.lower(county_name))
    
    print(included)
    
    if included: 
        return True, included
    else:
        return False, []
    
def is_zone_monitored(zones):
    for z in zones:
        if z in marine_regions:
            print(f"Alert located in Marine region.")
            return True
    print("Alert not located in specified marine region.")
    return False