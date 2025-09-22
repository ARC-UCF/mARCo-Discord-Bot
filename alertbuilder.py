
import requests
import global_vars
import zonemanager

globalRequestHeader = global_vars.globalRequestHeader

def retrieve_active():
    url = "https://api.weather.gov/alerts/active?area=FL"

    try:
        r = requests.get(url, headers=globalRequestHeader)  # keep as Response object
        if r.status_code != 200:
            print(f"⚠️ API returned status {r.status_code}: {r.text[:200]}")
            return []

        try:
            return r.json()
        except requests.exceptions.JSONDecodeError:
            print("⚠️ Response was not valid JSON!")
            print(f"Response text: {r.text[:200]}")  # Log first 200 chars
            return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request failed: {e}")
        return []
    
def retrieve_marine():
    url = "https://api.weather.gov/alerts/active?area=AM"
    
    try:
        r = requests.get(url, headers=globalRequestHeader)  # keep as Response object
        if r.status_code != 200:
            print(f"⚠️ API returned status {r.status_code}: {r.text[:200]}")
            return []

        try:
            return r.json()
        except requests.exceptions.JSONDecodeError:
            print("⚠️ Response was not valid JSON!")
            print(f"Response text: {r.text[:200]}")  # Log first 200 chars
            return []
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Request failed: {e}")
        return []
    
def fetch_alerts(): # Build index of alerts.

    if not zonemanager.ZONE_MAP: # If we have no zone map, we build one!!
        zonemanager.build_zone_map()

    r = retrieve_active()
    
    if not r or "features" not in r:
        return []
    
    marine = retrieve_marine()

    alerts = [];
    for feature in r["features"]: # Assembling our alerts.
        props = feature["properties"]
        geometry = feature["geometry"]
        parameters = props.get("parameters", {})
        nws_headline_list = parameters.get("NWSheadline", [])
        zones = props.get("affectedZones", {})
        eventCode = props.get("eventCode", {})
        hailThreat = parameters.get("hailThreat", [])
        windThreat = parameters.get("windThreat", [])
        maxWindGust = parameters.get("maxWindGust", [])
        maxHailSize = parameters.get("maxHailSize", [])
        tornadoDamageThreat = parameters.get("tornadoDamageThreat", [])
        thunderstormDamageThreat = parameters.get("thunderstormDamageThreat", [])
        WEAHandling = parameters.get("WEAHandling", [])
        tornadoDetection = parameters.get("tornadoDetection", [])
        coordinates = []
        if geometry:
            coordinates = geometry.get("coordinates", [])

        SAME_LIST = eventCode.get("SAME", [])
        NWS_LIST = eventCode.get("NationalWeatherService", [])

        if nws_headline_list:
            nws_headline = nws_headline_list[0]
        else:
            nws_headline = props.get("headline", "No title")

        if hailThreat:
            hailThreat = hailThreat[0]
        else:
            hailThreat = ""
        
        if windThreat:
            windThreat = windThreat[0]
        else:
            windThreat = ""
        
        if maxWindGust:
            maxWindGust = maxWindGust[0]
        else:
            maxWindGust = ""

        if maxHailSize:
            maxHailSize = maxHailSize[0]
        else:
            maxHailSize = ""

        if tornadoDamageThreat:
            tornadoDamageThreat = tornadoDamageThreat[0]
        else:
            tornadoDamageThreat = ""
        
        if thunderstormDamageThreat:
            thunderstormDamageThreat = thunderstormDamageThreat[0]
        else:
            thunderstormDamageThreat = ""

        if WEAHandling:
            WEAHandling = WEAHandling[0]
        else:
            WEAHandling = ""

        if tornadoDetection:
            tornadoDetection = tornadoDetection[0]
        else:
            tornadoDetection = ""

        included, counties = zonemanager.is_county_monitored(zones)

        if included: # Append if alert includes monitored counties.
            alerts.append({ # Assembling.
                "id": feature["id"],
                "sent": props.get("sent", ""),
                "expires": props.get("expires", ""),
                "title": nws_headline,
                "area_code": "land",
                "secondary_title": props.get("headline", "No secondary title"),
                "areaDesc": props.get("areaDesc", ""),
                "desc": props.get("description", "No description"),
                "link": props.get("instruction", ""),
                "same_code": SAME_LIST[0],
                "nws_listing": NWS_LIST[0],
                "status": props.get("status", ""),
                "certainty": props.get("certainty", ""),
                "severity": props.get("severity", ""),
                "urgency": props.get("urgency", ""),
                "senderName": props.get("senderName", ""),
                "response": props.get("response", ""),
                "event": props.get("event", "UNSPECIFIED"),
                "hailThreat": hailThreat,
                "windThreat": windThreat,
                "maxWindGust": maxWindGust,
                "maxHailSize": maxHailSize,
                "tornadoDamageThreat": tornadoDamageThreat,
                "thunderstormDamageThreat": thunderstormDamageThreat,
                "WEAHandling": WEAHandling,
                "tornadoDetection": tornadoDetection,
                "coords": coordinates,
                "counties": counties,
            }) # Assembled
        print(f"Alert ID: {feature['id']}")
        print(f"Alert type: {SAME_LIST[0]} / {NWS_LIST[0]}")
        print("Affected zones:", zones)
        print("Mapped zone names:", [zonemanager.ZONE_MAP.get(z, 'UNKNOWN') for z in zones])
        
    cat = False
    if marine and "features" in marine and cat == True:
        for marinef in marine["features"]:
            print("Collecting marine properties.")
            props = marinef["properties"]
            geometry = marinef["geometry"]
            parameters = props.get("parameters", {})
            nws_headline_list = parameters.get("NWSheadline", [])
            zones = props.get("affectedZones", {})
            eventCode = props.get("eventCode", {})
            coordinates = []
            if geometry:
                coordinates = geometry.get("coordinates", [])

            SAME_LIST = eventCode.get("SAME", [])
            NWS_LIST = eventCode.get("NationalWeatherService", [])

            if nws_headline_list:
                nws_headline = nws_headline_list[0]
            else:
                nws_headline = props.get("headline", "No title")
                
            if zonemanager.is_zone_monitored(zones):
                print("yippee")
                alerts.append({ # Assembling.
                    "id": feature["id"],
                    "sent": props.get("sent", ""),
                    "expires": props.get("expires", ""),
                    "area_code": "marine",
                    "title": nws_headline,
                    "secondary_title": props.get("headline", "No secondary title"),
                    "areaDesc": props.get("areaDesc", ""),
                    "desc": props.get("description", "No description"),
                    "link": props.get("instruction", ""),
                    "same_code": SAME_LIST[0],
                    "nws_listing": NWS_LIST[0],
                    "status": props.get("status", ""),
                    "certainty": props.get("certainty", ""),
                    "severity": props.get("severity", ""),
                    "urgency": props.get("urgency", ""),
                    "senderName": props.get("senderName", ""),
                    "response": props.get("response", ""),
                    "event": props.get("event", "UNSPECIFIED"),
                    "coords": coordinates,
                    "countes": [],
                }) # Assembled
            print(f"Affected zones ", zones) 
        
    print(alerts)
        
    return alerts