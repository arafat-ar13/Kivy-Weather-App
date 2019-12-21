import os

import geocoder
import requests
import pytz

import datetime

# Using OpenWeather API to handle weather forecast processing
API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BING_MAPS_KEY = os.environ.get("BING_MAPS_KEY")

def get_time_zone(city):
    r = requests.get(f"https://dev.virtualearth.net/REST/v1/TimeZone/?query={city}&key={BING_MAPS_KEY}")
    return r.json()["resourceSets"][0]["resources"][0]["timeZoneAtLocation"][0]["timeZone"][0]["ianaTimeZoneId"]

def night_or_day(city):
    tz = pytz.timezone(get_time_zone(city))
    datetime_tz = datetime.datetime.now(tz)
    time_hour = float(datetime_tz.strftime("%H.%M"))
    time = datetime_tz.strftime("%H:%M:%S")

    if time_hour >= 6 and time_hour <= 18:
        return time, "Day"
    else:
        return time, "Night"

def get_weather_data(city, country="", unit="imperial"):
    if country == "":
        r = requests.get(f"https://api.openweathermap.org/data/2.5/find?q={city}&appid={API_KEY}&units={unit}")
    else:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/find?q={city},{country}&appid={API_KEY}&units={unit}")

    try:
        time, day_night = night_or_day(city)
        for data in r.json()["list"]:
            name = data["name"]
            temperature = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            country = data["sys"]["country"]
            rain = data["rain"]
            snow = data["snow"]
            for info in data["weather"]:
                description = info["description"]

            return name, country, temperature, humidity, rain, snow, description, time, day_night
    except:
        return None

def auto_detect_loc():
    g = geocoder.ip("me")
    return get_weather_data(g.city, g.country)
