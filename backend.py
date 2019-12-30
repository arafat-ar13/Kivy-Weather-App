import datetime
import os
import socket

import geocoder
import pytz
import requests

# Using OpenWeather API and Bing Maps API
API_KEY = os.environ.get("OPENWEATHER_API_KEY")
BING_MAPS_KEY = os.environ.get("BING_MAPS_KEY")

def unit_converter(value, unit):
    if unit == "metric":
        val = (value * 9/5) + 32
        symbol = "F"
    elif unit == "imperial":
        val = (value - 32) * 5/9
        symbol = "C"

    return round(val, 2), symbol


def check_internet():
    """
    This method checks if an internet connect is present or not. If not, then the app will immediately let the user know that no internet connection is available.
    """
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection(("www.bing.com", 80))
        s.close()

        return True
    except:
        return False


def get_time_zone(city):
    r = requests.get(
        f"https://dev.virtualearth.net/REST/v1/TimeZone/?query={city}&key={BING_MAPS_KEY}")
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


def get_weather_data(city, country="", unit="imperial", symbol="F"):
    if country == "":
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/find?q={city}&appid={API_KEY}&units={unit}")
    else:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/find?q={city},{country}&appid={API_KEY}&units={unit}")

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

            return name, country, temperature, humidity, rain, snow, description, time, day_night, symbol
    except:
        return None


def auto_detect_loc(unit, symbol):
    g = geocoder.ip("me")
    return get_weather_data(unit=unit, symbol=symbol, city=g.city, country=g.country)
