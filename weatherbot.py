# libraries
# operated by skye
# contact skyechannelwrx on discord for questions or concerns
import discord 
import alertbuilder
import global_vars
import zonemanager
import forecastmanager
import shapehandler

from discord import app_commands
from discord import SyncWebhook
import asyncio
import datetime
from datetime import datetime, timezone, timedelta, time
from shapely.geometry import Point
import geopandas as gpd
import json
from dotenv import load_dotenv
load_dotenv("sensitive.env")

import os
import xml.etree.ElementTree as ET

LOCAL_TEST_MODE = False # Restrict testing information to main guild only.

VER_ID = global_vars.VersionID

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

roads_shp = r"C:\Users\sheri\OneDrive\Desktop\WeatherAlerts\ne_10m_roads_north_america.shp" # Natural Earth road shapefile path.
profile_picture = r"https://cdn.discordapp.com/attachments/1167929494147074098/1286378798366552184/image.png?ex=66ed0b40&is=66ebbac0&hm=5a3647a6dbb7e1f30c6d2b198f0e0862a77057a234d56708d4e7c1f2bb92d537&" # This doesn't particularly work, but whatever.
author = "ARC ALERTS @ UCF"

globalRequestHeader = global_vars.globalRequestHeader # Global header for all API requests made through the bot. Email is required. 

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

        alerts = alertbuilder.fetch_alerts()
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
                    buf = shapehandler.generate_alert_image(alert['coords'][0], temp_SAME) # Generate alert image.
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
                            alertSpace, type = shapehandler.ucf_in_or_near_polygon(alert["coords"][0])
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
            forecasts = forecastmanager.fetch_forecast()
        
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
            
            hurrImage, discussion = forecastmanager.get_hurricane_forecast()
        
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
    alerts = alertbuilder.fetch_alerts()
    if not alerts:
        await interaction.response.send_message("There are no active alerts!")
    else:
        array_members = len(alerts)
        await interaction.response.send_message(f"There are {array_members} active alerts!")

@client.tree.command(name="monitoring", description="Responds with Pong!")
async def monitoring(interaction: discord.Interaction):
    county_string = ", ".join(sorted(global_vars.counties))
    await interaction.response.send_message("I am currently monitoring the following counties: " + county_string)
    
client.run(TOKEN)