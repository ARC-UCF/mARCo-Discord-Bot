globalRequestHeader = {"User-Agent": "ARC ALERTS @ UCF (4noahsentelle@gmail.com)"}
VersionID = "1.1.0"

buffer_WEASTrigger = 3 # Within how many miles is our buffer?
alertCheck_Time = 90 # Time (in seconds) between each alert check. 

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