import datetime
import requests
import time


class Weather:
    def __init__(self, data: dict):
        # system data
        self.created_time = data["CreatedTime"]
        self.system_id = data["SystemID"]

        # heat/humidity data
        self.temperature: float = data["Temperature"]
        self.humidity: float = data["Humidity"]
        self.heat_index: int = data["HeatIndex"]
        self.heat_advisory_level: int = data["HeatAdvisoryLevel"]

        # wind data
        self.wind_speed: int = data["WindSpeed"]
        self.wind_direction: int = data["WindDirection"]
        self.cardinal_wind_direction: str = data["CardinalWindDirection"]
        self.wind_gust: int = data["WindGust"]

        # dew/rain data
        self.dew_point: float = data["Dewpoint"]
        self.rainfall: int = data["Rainfall"]

    def __str__(self):
        return f"As of {self.created_time}, the temperature is {self.temperature} with a humidity of {self.humidity}.\nThe heat advisory level is: {self.heat_advisory_level} (heat index: {self.heat_index}).\nWind speed is {self.wind_speed}, with gusts up to {self.wind_gust} traveling {self.cardinal_wind_direction} ({self.wind_direction} degrees)\nCurrent dew point is {self.dew_point} with {self.rainfall} rainfall."


class LightningStrike:
    def __init__(self, data: dict):
        # strike id info
        self.occurred: str = data["Occurred"]
        self.strike_id: int = data["StrikeID"]

        # distance & direction info
        self.distance: float = data["Distance"]
        self.direction: float = data["Direction"]

    def __str__(self):
        return f"Lightning strike recorded at {self.occurred}. {self.distance} miles at a heading of {self.direction} degree(s)."


class StrikeSummary:
    def __init__(self, data: dict):
        # system data
        self.created_time = data["CreatedTime"]
        self.system_id = data["SystemID"]

        self.friendly_advisory_level = data["FriendlyAdvisoryLevel"]

        # direction/strike data
        self.strike_count = data["StrikeCount"]
        self.strike_direction = data["StrikeDirection"]
        self.strike_distance = data["StrikeDistance"]

    def __str__(self):
        return f"Strike summary from {self.created_time}, overall advisory level is {self.friendly_advisory_level}.\nTotal Strikes: {self.strike_count}\nMost recent strike distance: {self.strike_distance}\nMost recent strike direction: {self.strike_direction}"


class ThorGuard:
    def __init__(self, system_id: int):
        self.system_id = system_id

        # variables to store last query in
        self.last_weather: Weather | None = None
        self.last_strike_summary: StrikeSummary | None = None

    def get_current_weather(self) -> Weather:
        # get the current weather status
        r = requests.get(
            f"https://360.thormobile.net/thorcloud/api/weatherpackets/GetBySystemID?ids={self.system_id}&ms={time.time()}")
        data = r.json()

        weather = Weather(data[list(data.keys())[0]])

        self.last_weather = weather

        return self.last_weather

    def get_current_strike_summary(self) -> StrikeSummary:
        # check current thor guard lightning status
        r = requests.get(
            f"https://360.thormobile.net/thorcloud/api/productionpackets/GetBySystemID?ids={self.system_id}&ms={time.time()}")
        data = r.json()

        summary = StrikeSummary(data[list(data.keys())[0]])

        self.last_strike_summary = summary

        return self.last_strike_summary

    def get_strike_list(self, time_span: float = 1800) -> list[LightningStrike]:
        # get a list of lightning strikes over the last (time span) seconds
        current_time = datetime.datetime.now()
        past_time = current_time - datetime.timedelta(seconds=time_span)

        # format times
        # 2025-07-20T16:02:39
        format_str = "%Y-%m-%dT%H:%M:%S"
        current_time_formatted = current_time.strftime(format_str)
        past_time_formatted = past_time.strftime(format_str)

        # send request
        r = requests.get(
            f"https://360.thormobile.net/thorcloud/api/strikes/getbysystemid?ids=3338&startTime={past_time_formatted}&endTime={current_time_formatted}"
        )
        data = r.json()

        # parse data
        data = data[str(self.system_id)]

        strikes = []
        for strike in data:
            strikes.append(LightningStrike(strike))

        return strikes


# create a new thor guard object
thor_guard = ThorGuard(3338)

print(thor_guard.get_current_weather())

print(thor_guard.get_current_strike_summary())

# get current weather
for strike in thor_guard.get_strike_list():
    print(strike)

# get current lightning advisory level
# print(thor_guard.get_current_strike_summary().friendly_advisory_level)
