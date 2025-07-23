# bot.py
import os
import pandas as pd
import discord
import openmeteo_requests
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv
from discord.ext import commands
import datetime
import pytz

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 300)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD = os.getenv('DISCORD_GUILD_NAME')

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} has connected!\n'
        f'{guild.name} (id: {guild.id})'
        )
    
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("hello bot" or "Hello bot"):
        await message.channel.send("Hello asshole")

    warsaw_tz = pytz.timezone('Europe/Warsaw')
    api_call_count = 0

    if message.content.startswith("!weather"):
        print(f"--- API Call Made ---")
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 52.2298,
            "longitude": 21.0118,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "daylight_duration"],
            "current": ["temperature_2m", "relative_humidity_2m", "precipitation", "rain", "showers", "snowfall"],
            "timezone": "Europe/Berlin",
            "forecast_days": 1,
            "timeformat": "unixtime"
        }
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # Current values. The order of variables needs to be the same as requested.
        current = response.Current()
        current_temperature_2m = current.Variables(0).Value()
        current_relative_humidity_2m = current.Variables(1).Value()
        current_precipitation = current.Variables(2).Value()
        current_rain = current.Variables(3).Value()
        current_showers = current.Variables(4).Value()
        current_snowfall = current.Variables(5).Value()

    # Convert Unix timestamp to human-readable time in Warsaw timezone
        unix_timestamp = current.Time()
        current_dt_utc = datetime.datetime.fromtimestamp(unix_timestamp, tz=datetime.timezone.utc)
        current_dt_warsaw = current_dt_utc.astimezone(warsaw_tz)
        formatted_current_time = current_dt_warsaw.strftime('%Y-%m-%d %H:%M %Z')

        daily = response.Daily()
        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()[0]
        daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()[0]
        daily_precipitation_probability_max = daily.Variables(2).ValuesAsNumpy()[0]
        daily_daylight_duration = daily.Variables(3).ValuesAsNumpy()[0]

        # Convert daylight_duration from seconds to hours and minutes
        daylight_hours = int(daily_daylight_duration // 3600)
        daylight_minutes = int((daily_daylight_duration % 3600) // 60)

        # --- Construct the human-readable output ---
        weather_output = (
            f"📍 **Weather in Warsaw, Poland**\n"
            f"🗓️ **As of:** {formatted_current_time}\n\n"
            f"**☁️ Current Conditions:**\n"
            f"  🌡️ Temperature: {current_temperature_2m:.1f}°C\n"
            f"  💧 Relative Humidity: {current_relative_humidity_2m:.0f}%\n"
            f"  🌧️ Precipitation (1h): {current_precipitation:.1f} mm\n"
            f"  ☔ Rain (1h): {current_rain:.1f} mm\n"
            f"  🚿 Showers (1h): {current_showers:.1f} mm\n"
            f"  ❄️ Snowfall (1h): {current_snowfall:.1f} cm\n\n" # Note: OpenMeteo often gives snowfall in cm for 1h
            f"**☀️ Today's Forecast:**\n"
            f"  ⬆️ Max Temp: {daily_temperature_2m_max:.1f}°C\n"
            f"  ⬇️ Min Temp: {daily_temperature_2m_min:.1f}°C\n"
            f"  💦 Precip. Prob: {daily_precipitation_probability_max}%\n"
            f"  🌅 Daylight: {daylight_hours}h {daylight_minutes}m\n"
        )
        await message.channel.send(weather_output)

client.run(TOKEN)