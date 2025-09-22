# libraries
# operated by skye
# contact skyechannelwrx on discord for questions or concerns
import discord 

from discord import app_commands
from discord import SyncWebhook
from io import BytesIO
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.io.shapereader import natural_earth, Reader
from cartopy.feature import ShapelyFeature
import requests
import asyncio
import datetime
from datetime import datetime, timezone, timedelta, time
from shapely.geometry import Point, Polygon
import geopandas as gpd
import re
import math
import json
import requests
from html.parser import HTMLParser
import re
import html
from dotenv import load_dotenv
load_dotenv("sensitive.env")

import os
import xml.etree.ElementTree as ET

LOCAL_TEST_MODE = False # Restrict testing information to main guild only.

VER_ID = "1.1.0"

TOKEN = os.environ.get("API-TOKEN")
GUILD_ID = 1402335501746311311 # skye club Guild Id

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
ARC_URL = os.environ.get("ARC_URL")
hurricane_URL = os.environ.get("hurricane_URL")
forecast_URL = os.environ.get("forecast_URL")
orange_URL = os.environ.get("orange_URL")
seminole_URL = os.environ.get("seminole_URL")
brevard_URL = os.environ.get("brevard_URL")
volusia_URL = os.environ.get("volusia_URL")
lake_URL = os.environ.get("lake_URL")
osceola_URL = os.environ.get("osceola_URL")
st_johns_URL = os.environ.get("st_johns_URL")
polk_URL = os.environ.get("polk_URL")
flagler_URL = os.environ.get("flagler_URL")
marine_URL = os.environ.get("marine_URL")

ARC_ID = 881444885402628177
webhook = SyncWebhook.from_url(WEBHOOK_URL) # Sync
web_hurricane = SyncWebhook.from_url(hurricane_URL) # Sync hurricane URL
web_orange = SyncWebhook.from_url(orange_URL) # Sync orange URL
web_seminole = SyncWebhook.from_url(seminole_URL) # Sync seminole URL
web_volusia = SyncWebhook.from_url(volusia_URL) # Sync volusia URL 
web_ARC = SyncWebhook.from_url(ARC_URL) # Sync ARC URL
web_brevard = SyncWebhook.from_url(brevard_URL) # Sync brevard URL
web_lake = SyncWebhook.from_url(lake_URL) # Sync lake URL
web_osceola = SyncWebhook.from_url(osceola_URL) # Sync osceola URL
web_st_johns = SyncWebhook.from_url(st_johns_URL) # Sync st. johns URL
web_polk = SyncWebhook.from_url(polk_URL) # Sync polk URL
web_flagler = SyncWebhook.from_url(flagler_URL) # Sync flagler URL
web_marine = SyncWebhook.from_url(marine_URL) # Sync marine URL
web_forecast = SyncWebhook.from_url(forecast_URL) # Sync forecast URL

posted_alerts = {} # Index of currently posted alerts. We clear this when an alert expires as to protect our memory.

ucf = Point(-81.2001, 28.6024) # UCF coords for shapely polygon checking
ucf_point = gpd.GeoSeries([Point(ucf)], crs="EPSG:4326") # Converting UCF to GeoSeries now so we aren't doing this over and over again for just one point.
ucf_point = ucf_point.to_crs(epsg=6439) # Convert to local CRS, this one being Florida East in meters.
buffer_WEASTrigger = 3 # Within how many miles is our buffer?
alertCheck_Time = 90 # Time (in seconds) between each alert check. 

forecastPosted = False
lastDate = None

wfo_grid_x = 26
wfo_grid_y = 68

roads_shp = r"\OneDrive\Desktop\WeatherAlerts\ne_10m_roads_north_america.shp" # Natural Earth road shapefile path. Full path present in actual code.
profile_picture = r"https://cdn.discordapp.com/attachments/1167929494147074098/1286378798366552184/image.png?ex=66ed0b40&is=66ebbac0&hm=5a3647a6dbb7e1f30c6d2b198f0e0862a77057a234d56708d4e7c1f2bb92d537&"
author = "ARC ALERTS @ UCF"

globalRequestHeader = {"User-Agent": "ARC ALERTS @ UCF ()"} # Global header for all API requests made through the bot. Email is required. Present in actual code.

# Actively monitored counties. Point must be in these counties in order to be alerted for.
# Uses FLC and FLZ areas, so any county added will be monitored, as long as it is within Florida.
counties = {
    "Orange, FL",
    "Seminole, FL",
    "Brevard, FL",
    "Volusia, FL",
    "Osceola, FL",
    "Lake, FL",
    "Polk, FL",
    "Flagler, FL",
    "St. Johns, FL",
    "Indian River, FL",
}

marine_regions = {
    "https://api.weather.gov/zones/forecast/AMZ552", # Volusia-Brevard County line to Sebastian Inlet out 0-20 nautical miles.
    "https://api.weather.gov/zones/forecast/AMZ550", # Flagler Beach to Volusia-Brevard county line out 0-20 nautical miles.
    "https://api.weather.gov/zones/forecast/AMZ454",
    
}

alertCodes = {
    "TOR",
    "SVR",
    "SVA",
    "TOA",
    "FFW",
    "HUW",
    "TRW",
    "FLW",
    "SVS",
    "BLU",
    "CAE",
    "CDW",
    "CEM",
    "EQW",
    "EVI",
    "FRW",
    "HMW",
    "LEW",
    "LAE",
    "TOE",
    "NUW",
    "RHW",
    "SPW",
    "ADR",
    "TSW",
}

message_refs = {
    "TOR": f"A Tornado Warning has been issued for the UCF area! Check local media.",
    "SVR": f"A Severe Thunderstorm Warning has been issued for the UCF area! Seek shelter inside a sturdy building. Severe thunderstorms may produce wind gusts of 58 mph or higher or hail 1 inch in diameter or greater!",
    "SVA": f"The Storm Prediction Center has issued a Severe Thunderstorm Watch for the UCF area! Monitor the weather. Weather conditions can change rapidly. Adhere to advisories and warnings issued by the National Weather Service. Inform friends and families.",
    "TOA": f"The Storm Prediction Center has issued a Tornado Watch for the UCF area! Monitor the weather. Weather conditions can change rapidly. Adhere to advisories and warnings issued by the National Weather Service. Inform friends and families.",
    "SPS": f"A Special Weather Statement has been issued for the UCF area! Seek shelter inside a sturdy building. This is a strong storm: wind gusts 40 to 50 mph and/or small hail are possible with this storm.",
    "FFW": f"A Flash Flood Warning has been issued for the UCF area! Flooding may be dangerous. Avoid flooded roads, especially at night. Remember: turn around, don't drown! Report flooding to the National Weather Service.",
    "FAY": f"A Flood Advisory has been issued for the UCF area. Minor flooding of roads and low-lying areas is possible. Avoid flooded roads, especially at night. Remember: turn around, don't drown!",
    "FLW": f"A Flood Warning has been issued for the UCF area. Flooding of roads and low-lying areas is possible. Avoid flooded roads, especially at night. Remember: turn around, don't drown!",
    "TRA": f"A Tropical Storm Watch has been issued for the UCF area. A Tropical Storm Watch means Tropical Storm conditions - sustained winds 39-73 mph - are possible in the next 48 hours.",
    "TRW": f"A Tropical Storm Warning has been issued for the UCF area. A Tropical Storm Warning means Tropical Storm conditions - sustained winds 39-73 mph - are expected in the next 36 hours or sooner.",
}

severity_colors = { # This severity index is based on the severity property in alerts.
    "Extreme": 0xA020F0,   # Purple
    "Severe": 0xFF0000,    # Red
    "Moderate": 0xFFA500,  # Orange
    "Minor": 0xFFFF00,     # Yellow
    "Unknown": 0x808080    # Gray
}

polygon_colors_SAME = {
    "TOR": '#d900ff',
    "SVR": '#ffb300',
    "FFW": '#00bf03',
    "SPS": '#0086bf',
    "FAY": '#00ff8c',
    "FLW": '#00ff40',
    "FLS": '#00ff40',
} # SMW/MAW for Special Marine Warning

ZONE_MAP = {}

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync slash commands to your server
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = MyClient()

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
    
def retrieve_forecast():
    url = "https://api.weather.gov/gridpoints/MLB/26,68/forecast?units=us"
    
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
    
def get_hurricane_forecast(xml_content=None):
    """
    Fetches the Atlantic 7-day outlook image URL and discussion text from the NHC RSS feed.
    If xml_content is provided, parses from that string instead of fetching from the web.
    Returns (image_url, formatted_discussion_text)
    """
    rss_url = "https://www.nhc.noaa.gov/gtwo.xml"
    if xml_content is None:
        response = requests.get(rss_url)
        response.raise_for_status()
        xml_content = response.content

    root = ET.fromstring(xml_content)

    image_url = None
    discussion_text = None

    # Find the Atlantic Outlook item
    for item in root.findall(".//item"):
        title = item.findtext("title")
        if title and "Atlantic Outlook" in title:
            description = item.findtext("description")
            if description:
                # Extract the 7-day image URL from the description
                match = re.search(r'<img\s+src="([^"]+)"\s+alt="Atlantic 7-Day Graphical Outlook Image"', description)
                if match:
                    image_url = match.group(1)
                # Extract the discussion text (strip HTML tags)
                # The discussion is inside <div class='textproduct'>...</div>
                discussion_match = re.search(
                    r"<div class='textproduct'>(.*?)</div>", description, re.DOTALL
                )
                if discussion_match:
                    discussion_html = discussion_match.group(1)
                    # Format the HTML text for Discord
                    discussion_text = format_nhc_html(discussion_html)
            break
    return image_url, discussion_text

def format_nhc_html(html_text):
    """
    Converts NHC HTML text to Discord-friendly markdown.
    - <br> becomes newlines
    - Remove other HTML tags
    - Unescape HTML entities
    """

    # Replace <br> and <br/> with newlines
    text = re.sub(r'<br\s*/?>', '\n', html_text, flags=re.IGNORECASE)
    # Remove all other HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Unescape HTML entities
    text = html.unescape(text)
    # Remove leading/trailing whitespace and collapse multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text
    
def fetch_alerts(): # Build index of alerts.

    if not ZONE_MAP: # If we have no zone map, we build one!!
        build_zone_map()

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

        included, counties = is_county_monitored(zones)

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
        print("Mapped zone names:", [ZONE_MAP.get(z, 'UNKNOWN') for z in zones])
        
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
                
            if is_zone_monitored(zones):
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

def fetch_forecast():
    r = retrieve_forecast()
    
    if not r or "properties" not in r:
        return []
    
    forecastInfo = []
    props = r["properties"]
    periods = props["periods"]
    
    forecastInfo.append(periods[0])
    forecastInfo.append(periods[1])
    forecastInfo.append(periods[2])
    forecastInfo.append(periods[3])
    
    return forecastInfo
        
    

def ucf_in_or_near_polygon(geodat): # Specific to figuring out if UCF is included or near the alert polygon, only for WEAS handling.
    if not geodat:
        return False, ""
    
    poly = Polygon(geodat)

    if ucf.within(poly):
        return True, "within"
    else: # Handle logic to find out if this alert polygon is near UCF.
        gdf_alert = gpd.GeoSeries([poly], crs="EPSG:4326")

        gdf_alert = gdf_alert.to_crs(epsg=6439)  # NAD83 / Florida East (meters)

        # Buffer UCF point by 3 miles (1 mile ≈ 1609.34 m)
        pBuffer = ucf_point.buffer(3 * 1609.34)

        # Check if alert polygon intersects the buffered area
        intersects = gdf_alert.intersects(pBuffer.iloc[0])[0]

        if intersects:
            return True, "around"
    return False, ""

def get_bounds_from_polygon(polygon_coords, buffer_miles=0):
    lons, lats = zip(*polygon_coords)  # unzip into separate lists
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    if buffer_miles > 0:
        # 1 mile ~ 0.0145 degrees latitude
        lat_buffer = buffer_miles * 0.0145
        avg_lat = sum(lats) / len(lats)
        # adjust longitude for latitude
        lon_buffer = buffer_miles * 0.0145 / max(0.0001, abs(math.cos(math.radians(avg_lat))))
        
        min_lon -= lon_buffer
        max_lon += lon_buffer
        min_lat -= lat_buffer
        max_lat += lat_buffer

    return min_lon, max_lon, min_lat, max_lat


def filter_points_in_bounds(points, bounds):
    """
    points: list of tuples (name, lon, lat)
    bounds: min_lon, max_lon, min_lat, max_lat
    returns: filtered list of points inside bounds
    """
    min_lon, max_lon, min_lat, max_lat = bounds
    filtered = []
    for name, lon, lat in points:
        if min_lon <= lon <= max_lon and min_lat <= lat <= max_lat:
            filtered.append((name, lon, lat))
    return filtered

def generate_alert_image(coords, code): # function to generate an image for the alert area.
    if not coords: # Gating. Return false if we don't have coords (in cases where alerts are for county and have no geodata)
        return False 
    
    city_points = [ # Expand to include locations as needed. Maybe want a secondary list for more minor locations?
        ("Orlando", -81.379, 28.538),
        ("Oviedo", -81.204, 28.669),
        ("Bithlo", 	-81.11016, 28.5632373),
        ("MCO", -81.308, 28.431),
        ("Winter Park", -81.348, 28.599),
        ("Lake Mary", -81.347, 28.777),
        ("Sanford", -81.291, 28.802),
        ("UCF", -81.2023, 28.6024),
        ("Apopka", -81.5322149, 28.6934076),
        ("Lake Nona", -81.2639123, 28.3976142),
        ("Doctor Phillips", -81.4914804, 28.4608599),
        ("Casselberry", -81.3382005, 28.6714702),
        ("Rosen", -81.4421618, 28.4290395),
        ("Ocoee", -81.5441944, 28.5694468),
        ("Wedgefield", -81.0776654, 28.4853741),
        ("Christmas", -80.9977987, 28.520462),
        ("Hunter's Creek", -81.421598, 28.3568574),
        ("Titusville", -80.8075537, 28.6122187),
        ("Melbourne", -80.6081089, 28.0836269),
        ("Palm Bay", -80.5886646, 28.0344621),
        ("Cape Canaveral", -80.6077132, 28.3922182),
        ("Rockledge", -80.736647, 28.3201553),
        ("Viera", -80.7301522, 28.243006),
        ("Clermont", -81.7728543, 28.5494447),
        ("Eustis", -81.6853534, 28.8527675),
        ("Mount Dora", -81.6458572379921, 28.81874675),
        ("Kissimmee", -81.407571, 28.2919557),
        ("St. Cloud", -81.2839038, 28.2498534),
        ("Harmony", -81.1450659, 28.1894586),
        ("Holopaw", -81.0761754, 28.1358492),
        ("Astor Park", -81.5720175, 29.1535911),
        ("Seville", -81.4925714, 29.3169208),
        ("Ormond Beach", -81.0557921, 29.2854132),
        ("Daytona Beach", -81.0228331, 29.2108147),
        ("Port Orange", -81.0105961760805, 29.10162805),
        ("DeLand", -81.3031098, 29.0283213),
        ("Deltona", -81.2636738, 28.9005446),
        ("New Smyrna Beach", -80.9269984, 29.0258191),
        ("Scottsmoor", -80.87811, 28.7669363),
        ("Satellite Beach", -80.5900519, 28.1761233),
        ("Yeehaw Junction", -80.9043171, 27.6997754),
        ("Lakeland", -81.9498042, 28.0394654),
        ("Highland Park", -81.5617427, 27.8650254),
        ("Polk City", -81.8239676, 28.1825147),
        ("Poinciana", -81.4932235, 28.1743275),
        ("Winter Haven", -81.7328567, 28.0222435),
        ("Homeland", -81.8245267, 27.8178061),
        ("Bradley Junction", -81.9803629, 27.7953069),
        ("Frostproof", -81.5306313, 27.7458626),
        ("Indian Lake Estates", -81.3786902, 27.8141828),
        ("Bartow", -81.8431567, 27.8963791),
        ("Fruit Cove", -81.6069919, 30.0928745),
        ("Saint Augustine", -81.3124341, 29.9012437),
        ("Saint Augustine Beach", -81.2716634, 29.8508613),
        ("Hartford", -81.5065599, 30.0156817),
        ("Palmo", -81.5673077, 29.9663545),
        ("Old Town Villages", -81.3996685, 29.9103519),
        ("Crescent Beach", -81.2423048, 29.738289),
        ("Hastings", -81.5081338, 29.7180248),
        ("Shell Bluff", -81.4925332, 29.5071816),
        ("Myrtle Island", -81.441184, 29.5855272),
        ("Palm Coast", -81.2078699, 29.5844524),
        ("Dupont", -81.2225622, 29.4269207),
        ("Codys Corner", -81.3110131, 29.3433587),
        ("Flagler Beach", -81.1269982, 29.4749927),
        ("Bunnell", -81.2576832, 29.4657731),
        ("Fellsmere", -80.6013691, 27.7677894),
        ("Sebastian", -80.4706078, 27.816415),
        ("Indian River Shores", -80.3781423, 27.7124084),
        ("Vero Beach", -80.3972736, 27.6386434),
        ("Oslo", -80.3807842, 27.587099),
        ("Lakewood Park", -80.3858334, 27.539169),
        ("Bayside Lakes", -80.6665445, 27.9488718),
        ("Grant-Valkaria", -80.5773329, 27.9378067),
        ("Deer Run", -80.6500523, 27.8713665),
        ("Micco", -80.5052124, 27.8639584),
        ("Port Saint John", -80.7859151, 28.476174),
        ("Mims", -80.8457402, 28.683293),
    ]

    poly = Polygon(coords)

    minx, miny, maxx, maxy = poly.bounds
    
    if not poly:
        return False

    fig, ax = plt.subplots(
        figsize=(14, 10),
        subplot_kw={'projection': ccrs.PlateCarree()}
    )

    # Applying overlays
    ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.LAKES.with_scale('10m'), facecolor='lightblue')
    ax.add_feature(cfeature.RIVERS.with_scale('10m'), edgecolor='blue')
    ax.add_feature(cfeature.BORDERS.with_scale('10m'), edgecolor='black')
    ax.add_feature(cfeature.STATES.with_scale('10m'), edgecolor='black')

   # Counties (Natural Earth Admin 2)
    counties_shp = natural_earth(resolution='10m', category='cultural', name='admin_2_counties')
    counties_feature = ShapelyFeature(
        geometries=Reader(counties_shp).geometries(),
        crs=ccrs.PlateCarree(),
        facecolor='none',
        edgecolor='red',
        linewidth=1
    )
    if counties_feature is not None:
        ax.add_feature(counties_feature)

    roads_feature = ShapelyFeature(
        Reader(roads_shp).geometries(),
        crs=ccrs.PlateCarree(),
        edgecolor='grey',  # whatever color you like
        facecolor='none'
    )
    if roads_feature is not None:
        ax.add_feature(roads_feature)
    
    polyColor = '#6e6e6e'
    
    if code in polygon_colors_SAME:
        polyColor = polygon_colors_SAME[code]

    # Plot polygon
    x, y = poly.exterior.xy
    ax.plot(x, y, color=polyColor, linewidth=2, transform=ccrs.PlateCarree())
    ax.fill(x, y, color=polyColor, alpha=0.2, transform=ccrs.PlateCarree())

    # Zoom to polygon with padding
    lon_pad = 0.5  # wider east-west
    lat_pad = 0.25  # shorter north-south
    ax.set_extent([minx - lon_pad, maxx + lon_pad, miny - lat_pad, maxy + lat_pad], crs=ccrs.PlateCarree())
    # we love rectangles btw

    bounds = get_bounds_from_polygon(coords, 15)

    filtered_points = filter_points_in_bounds(city_points, bounds)

    for name, lon, lat in filtered_points:
        ax.scatter(lon, lat, color='blue', s=45, transform=ccrs.PlateCarree())
        ax.text(lon, lat + 0.01, name, fontsize=9, transform=ccrs.PlateCarree())

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf  # Return image


@client.event
async def on_ready():
    channel = client.get_channel(1402335502215942310)

    print(f"Logged in as {client.user}")
    await channel.send(f"Ready to receive alerts.\nAlerts are checked for every {alertCheck_Time} seconds.")
    posted_alerts = {}
    forecastPosted = False
    afternoonPosted = False
    eveningPosted = False
    
    hurricane_Posted_Morning = False
    hurricane_Posted_Afternoon = False
    hurricane_Posted_Evening = False
    hurricane_Posted_Night = False
    
    lastDate = None
    try:
        with open("posted_alerts.json") as f:
            data = json.load(f)
            print("File found")
            print(data)
    except FileNotFoundError:
        print("File not found.")
        data = {"last_id": 0, "alerts": {}, "forecastPosted": False, "afternoonPosted": False, "eveningPosted": False, "hurricane_Posted_Morning": False, "hurricane_Posted_Afternoon": False, "hurricane_Posted_Evening": False, "hurricane_Posted_Night": False,"lastDate": None}
    if LOCAL_TEST_MODE:
        print(f"⚠️⚠️⚠️ LOCAL TEST MODE ENABLED; NOT PUSHING ALERTS ⚠️⚠️⚠️")

    posted_alerts = data["alerts"]
    last_id = data["last_id"]
    forecastPosted = data["forecastPosted"]
    afternoonPosted = data["afternoonPosted"]
    eveningPosted = data["eveningPosted"]
    hurricane_Posted_Morning = data["hurricane_Posted_Morning"]
    hurricane_Posted_Afternoon = data["hurricane_Posted_Afternoon"]
    hurricane_Posted_Evening = data["hurricane_Posted_Evening"]
    hurricane_Posted_Night = data["hurricane_Posted_Night"]
    lastDate = data["lastDate"]
    
    while True:
        now = datetime.now(timezone.utc)

        alerts = fetch_alerts()
        if alerts:
            for alert in alerts:
                alert_id = alert["id"]
                alert_sent = alert["sent"]

                if alert_id in posted_alerts:
                    # expiry update
                    if posted_alerts[alert_id]["expires"] != alert["expires"]:
                        posted_alerts[alert_id]["expires"] = alert["expires"]
                        print(f"Updated expiry for alert {alert_id}")

                    # update
                    if posted_alerts[alert_id]["sent"] != alert_sent:
                        posted_alerts[alert_id]["sent"] = alert_sent
                        label = " (Updated)"
                        print("Alert has been updated.")
                    else:
                        continue
                else:
                    # new alert → increment trackid
                    last_id += 1
                    
                    posted_alerts[alert_id] = {
                        "trackid": last_id,
                        "sent": alert_sent,
                        "expires": alert["expires"],
                        "areaDesc": alert["areaDesc"],
                        "event": alert["event"],
                    }
                    label = ""
                    print(f"Posting new alert with trackid {last_id}")
                description = "\n\n".join(filter(None, [alert['secondary_title'], alert['desc']]))

                severity = alert.get("severity", "Unknown")
                color = severity_colors.get(severity, 0x808080) # Determine color based on severity property.

                buf = 0
                temp_SAME = alert['same_code']
                
                if temp_SAME == "NWS":
                    temp_SAME = alert['nws_listing']
                
                if alert['coords']:
                    buf = generate_alert_image(alert['coords'][0], temp_SAME) # Generate alert image.
                file = ""

                embed = discord.Embed(
                    title=alert["title"] + label,
                    description=description,
                    color=color
                )

                embed.set_footer(text=f"ALERT TRACK ID #{last_id} // VER {VER_ID}")

                if buf: #Filter for if we have a file or not.
                    file = discord.File(fp=buf, filename="alert_map.png")
            
                    embed.set_image(url="attachment://alert_map.png")
                if alert["link"]:
                    embed.add_field(name="Instructions", value=alert["link"], inline=False)
            
                information = (
                f"Alert ID: {alert_id}\n"
                f"SAME: {alert['same_code']}\n"
                f"NWS Listing: {alert['nws_listing']}\n"
                f"Sender: {alert['senderName']}\n"
                f"Severity: {alert['severity']}\n"
                f"Urgency: {alert['urgency']}\n"
                f"Response: {alert['response']}\n"
                f"Certainty: {alert['certainty']}"
                )

                # Honestly I wonder if the entire thing I have below here could just be thrown together into one. 

                if alert["same_code"] != "SMW" and alert["nws_listing"] != "MWS":
                    if alert["hailThreat"]:
                        inputString = f"Hail Threat: {alert['hailThreat']}"
                        information = "\n".join(filter(None, [information, inputString]))

                    if alert["maxHailSize"]:
                        inputString = f"Max Hail Size: {alert['maxHailSize']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                    if alert["windThreat"]:
                        inputString = f"Wind Threat: {alert['windThreat']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                    if alert["maxWindGust"]:
                        inputString = f"Max Wind Gust: {alert['maxWindGust']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                    if alert["tornadoDamageThreat"]:
                        inputString = f"Damage Tag: {alert['tornadoDamageThreat']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                    if alert["tornadoDetection"]:
                        inputString = f"Threat indication: {alert['tornadoDetection']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                    if alert["thunderstormDamageThreat"]:
                        inputString = f"Damage Tag: {alert['thunderstormDamageThreat']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                    if alert["WEAHandling"]:
                        inputString = f"WEAS Handling: {alert['WEAHandling']}"
                        information = "\n".join(filter(None, [information, inputString]))    

                if information:
                    embed.add_field(name="Alert Information", value=information, inline=False)

                if buf: # Filter again.
                    msg = await channel.send(embed=embed, file=file)
                else:
                    msg = await channel.send(embed=embed)
                    
                await msg.publish()
                
                if alert["counties"]:
                    affected = alert["counties"]
                    if "orange" in affected:
                        print("Orange County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            print("Ping for alert.")
                            web_orange.send(f"<@&1406352173159288885>", username=author, avatar_url=profile_picture)
                        
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_orange.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_orange.send(embed=embed, username=author, avatar_url=profile_picture)
                        if alert["coords"]:
                            alertSpace, type = ucf_in_or_near_polygon(alert["coords"][0])
                            if alertSpace and type == "within":
                                if alert["same_code"] in alertCodes:
                                    web_ARC.send(f"<@&1406351918686539857>", username=author, avatar_url=profile_picture)
                                    print("Triggered by alert with valid SAME code.")
                                
                                buf.seek(0)
                                file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                                web_ARC.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            if alert["same_code"] in alertCodes:
                                web_ARC.send(f"<@&1406351918686539857>", username=author, avatar_url=profile_picture)
                                print("Triggered by alert with valid SAME code.")
                            
                            web_ARC.send(embed=embed, username=author, avatar_url=profile_picture)
                            print("UCF is assumed to be affected due to Orange County being listed.") # UCF is in Orange County; therefore, if the entire county is affected, UCF is affected. We will need to post to the ARC alert channel.
                    if "seminole" in affected:
                        print("Seminole County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_seminole.send("<@&1406352308819726577>", username=author, avatar_url=profile_picture)
                        
                        if buf: 
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_seminole.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_seminole.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "volusia" in affected:
                        print("Volusia County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_volusia.send("<@&1408164749803257946>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_volusia.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_volusia.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "brevard" in affected:
                        print("Brevard County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_brevard.send("<@&1406352415137075240>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_brevard.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_brevard.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "lake" in affected:
                        print("Lake County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_lake.send("<@&1408164919672832010>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_lake.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_lake.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "osceola" in affected:
                        print("Osceola County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_osceola.send("<@&1408165007417671731>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_osceola.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_osceola.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "polk" in affected:
                        print("Polk County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_polk.send("<@&1413975730261332068>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_polk.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_polk.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "st. johns" in affected:
                        print("St. Johns County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_st_johns.send("<@&1413676122788593828>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_st_johns.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_st_johns.send(embed=embed, username=author, avatar_url=profile_picture)
                    if "flagler" in affected:
                        print("Flagler County is affected by this alert.")
                        if alert["same_code"] in alertCodes:
                            web_flagler.send("<@&1414269696508956764>", username=author, avatar_url=profile_picture)
                            
                        if buf:
                            buf.seek(0)
                            file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                            web_flagler.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                        else:
                            web_flagler.send(embed=embed, username=author, avatar_url=profile_picture)
                if alert["area_code"] == "marine":
                    print("Marine alert detected.")
                    
                    if buf:
                        buf.seek(0)
                        file_for_webhook = discord.File(fp=buf, filename="alert_map.png")
                        web_marine.send(embed=embed, file=file_for_webhook, username=author, avatar_url=profile_picture)
                    else:
                        web_marine.send(embed=embed, username=author, avatar_url=profile_picture)
                          
                print(f"✅🔗 Alert pushed.")

                print("Sent alert " + alert_id)
        else:
            print(f"⚠️⚠️⚠️ NOTICE: NO ALERTS TO FILTER. ⚠️⚠️⚠️")
        expired = [aid for aid, data in posted_alerts.items() if data.get("expires") and datetime.fromisoformat(data["expires"]) < now]
        for aid in expired:
            if data.get("expires") and datetime.fromisoformat(data["expires"]) >= datetime.fromisoformat(data["expires"]) + timedelta(hours=1, minutes=30):
                print("in range")
            print(data)
            print(posted_alerts[aid])
            del posted_alerts[aid]
            print(f"🗑 Removed expired alert {aid}")
        if LOCAL_TEST_MODE:
            print(f"⚠️⚠️⚠️ REMINDER: LOCAL TEST MODE ENABLED: NOT PUSHING ALERTS.") # Reminder that I'm not pushing alerts because I'm a silly goose and sometimes forget to turn stuff off
            
        start = time(9, 0)
        end = time(9, 30)
        
        aStart = time(13,0)
        aEnd = time(13,30)
        
        eStart = time(20,0)
        eEnd = time(20,30)
        
        now = datetime.now()
        
        print(now)
        print(forecastPosted)
        print(afternoonPosted, eveningPosted)
            
        if (start <= now.time() <= end and not forecastPosted) or (aStart <= now.time() <= aEnd and not afternoonPosted) or (eStart <= now.time() <= eEnd and not eveningPosted):
            forecasts = fetch_forecast()
        
            if forecasts:
                embed = discord.Embed(
                    title="Forecast, Courtesy of NWS Melbourne",
                    color=0x53eb31,
                )
            
                embed.set_footer(text=f"VER {VER_ID}")
            
                for day in forecasts:
                    dName = day.get("name", "N/A")
                    temp = day.get("temperature", 0)
                    print(temp)
                    precipChance = day.get("probabilityOfPrecipitation", [])
                    probability = precipChance.get("value", 0)
                    windDirection = day.get("windDirection", "N/A")
                    shortForecast = day.get("shortForecast", "N/A")
                    detailedForecast = day.get("detailedForecast", "N/A")
                    fStartTime = day.get("startTime", "N/A")
                    fEndTime = day.get("endTime", "N/A")
                    
                    fsTimeStr = datetime.fromisoformat(fStartTime)
                    feTimeStr = datetime.fromisoformat(fEndTime)
                    
                    windSpeed = day.get("windSpeed", [])
                    print("WIND SPEED WIND SPEED")
                    print(windSpeed)
                    forecastString = f"Temperature: {temp}\nProbability of Rain: {probability}%\nWind: {windDirection} {windSpeed}\n\nForecast: {detailedForecast}"
                    print(f"FORECAST DETAILS {dName}\n{forecastString}")
                    
                    fullName = f"{dName} {fsTimeStr.date()} {fsTimeStr.time()} - {feTimeStr.date()} {feTimeStr.time()}"
                    
                    embed.add_field(name=fullName, value=forecastString, inline=False)
                
                msg = await channel.send(embed=embed)
                web_forecast.send(embed=embed, username=author, avatar_url=profile_picture)
                
                if start <= now.time() <= end:
                    print("Forecast posted")
                    forecastPosted = True
                if aStart <= now.time() <= aEnd:
                    print("Afternoon forecast posted")
                    afternoonPosted = True
                if eStart <= now.time() <= eEnd:
                    print("Evening forecast posted")
                    eveningPosted = True
                    
                    
        hurStartNight = time(2,30)
        hurEndNight = time(3,0)
                    
        hurStartMorning = time(8,30)
        hurEndMorning = time(9,0)
        
        hurStartAfternoon = time(14,30)
        hurEndAfternoon = time(15,0)
        
        hurStartEvening = time(20,30)
        hurEndEvening = time(21,0)
        
        if (hurStartNight <= now.time() <= hurEndNight and not hurricane_Posted_Night) or (hurStartMorning <= now.time() <= hurEndMorning and not hurricane_Posted_Morning) or (hurStartAfternoon <= now.time() <= hurEndAfternoon and not hurricane_Posted_Afternoon) or (hurStartEvening <= now.time() <= hurEndEvening and not hurricane_Posted_Evening) and (6 <= datetime.now().month <= 11):
            
            hurrImage, discussion = get_hurricane_forecast()
        
            embed = discord.Embed(
                title="Atlantic Hurricane Discussion",
                description=discussion,
                color=0x1e90ff,
            )
        
            embed.set_footer(text=f"VER {VER_ID} // Info from the National Hurricane Center")
            embed.set_image(url=hurrImage)
                    
            web_hurricane.send(embed=embed, username=author, avatar_url=profile_picture)
            
            if hurStartNight <= now.time() <= hurEndNight:
                print("Hurricane discussion posted night")
                hurricane_Posted_Night = True
            if hurStartMorning <= now.time() <= hurEndMorning:
                print("Hurricane discussion posted morning")
                hurricane_Posted_Morning = True
            if hurStartAfternoon <= now.time() <= hurEndAfternoon:
                print("Hurricane discussion posted afternoon")
                hurricane_Posted_Afternoon = True
            if hurStartEvening <= now.time() <= hurEndEvening:
                print("Hurricane discussion posted evening")
                hurricane_Posted_Evening = True
                    
        today = str(datetime.now().date())
        
        if not lastDate:
            lastDate = today
    
        if lastDate != today:
            print("new day! reset")
            print(lastDate)
            lastDate = today
            print(lastDate, today)
            forecastPosted = False
            afternoonPosted = False
            eveningPosted = False
            hurricane_Posted_Morning = False
            hurricane_Posted_Afternoon = False
            hurricane_Posted_Evening = False
            hurricane_Posted_Night = False
            
        with open("posted_alerts.json", "w") as f:
            json.dump({"last_id": last_id, "alerts": posted_alerts, "forecastPosted": forecastPosted, "afternoonPosted": afternoonPosted, "eveningPosted": eveningPosted, "hurricane_Posted_Morning": hurricane_Posted_Morning, "hurricane_Posted_Afternoon": hurricane_Posted_Afternoon, "hurricane_Posted_Evening": hurricane_Posted_Evening, "hurricane_Posted_Night": hurricane_Posted_Night, "lastDate": lastDate}, f, indent=2)
        
        print("hamburger")
        print(f"Status normal // operating on version {VER_ID}")
        await asyncio.sleep(alertCheck_Time)
            
# Misc bot commands to have fun with.

@client.tree.command(name="ping", description="Responds with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@client.tree.command(name="activealerts", description="Check how many (in number) of active alerts there are.")
async def activealerts(interaction: discord.Interaction):
    alerts = fetch_alerts()
    if not alerts:
        await interaction.response.send_message("There are no active alerts!")
    else:
        array_members = len(alerts)
        await interaction.response.send_message(f"There are {array_members} active alerts!")

@client.tree.command(name="monitoring", description="Responds with Pong!")
async def monitoring(interaction: discord.Interaction):
    county_string = ", ".join(sorted(counties))
    await interaction.response.send_message("I am currently monitoring the following counties: " + county_string)
    

client.run(TOKEN)

