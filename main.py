import os
import sys
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# ==========================================
# 1. LOGGING CONFIGURATION
# ==========================================
# This sets up the Python logging module to output formatted logs to the console.
# It helps you monitor the bot's status and debug any issues if the API fails.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger('WeatherBot')

# ==========================================
# 2. ENVIRONMENT VARIABLES
# ==========================================
# load_dotenv() reads the hidden .env file in the same directory.
# We extract the DISCORD_BOT_TOKEN securely so it's not hardcoded in the script.
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not TOKEN:
    # If the token is missing, the bot cannot start. Log a critical error and exit.
    logger.critical("DISCORD_BOT_TOKEN environment variable not set. Exiting.")
    sys.exit(1)

# ==========================================
# 3. UTILITIES & DATA MAPPING
# ==========================================
# Open-Meteo returns weather conditions as an integer code (e.g., 0, 61, 95).
# This dictionary maps those raw integer codes to human-readable strings.
WMO_CODES = {
    0: 'Clear Sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
    45: 'Foggy', 46: 'Rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
    55: 'Dense drizzle', 56: 'Light freezing drizzle', 57: 'Dense freezing drizzle',
    61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain', 71: 'Slight snow fall',
    73: 'Moderate snow fall', 75: 'Heavy snow fall', 77: 'Snow grains',
    80: 'Slight rain showers', 81: 'Moderate rain showers', 82: 'Violent rain showers',
    85: 'Slight snow showers', 86: 'Heavy snow showers', 95: 'Thunderstorms',
    96: 'Thunderstorms with slight hail', 99: 'Thunderstorms with heavy hail'
}

def format_weather_code(code: int) -> str:
    """Takes the raw WMO integer code and returns the readable weather description."""
    return WMO_CODES.get(int(code), "Unknown weather code")

def format_unix_timestamp(unix_timestamp: int, timezone_str: str) -> str:
    """
    Converts the raw Unix timestamp provided by the Open-Meteo API into a 
    readable date and time string based on the city's specific timezone.
    """
    try:
        dt = datetime.fromtimestamp(unix_timestamp, tz=timezone.utc).astimezone(ZoneInfo(timezone_str))
        return dt.strftime('%Y-%m-%d %H:%M %Z')
    except Exception as e:
        logger.error(f"Error formatting timestamp {unix_timestamp}: {e}")
        return "Unknown Time"

# ==========================================
# 4. DISCORD BOT INITIALIZATION
# ==========================================
# We define the basic permissions (intents) the bot needs.
# `message_content = True` is strictly required to read commands starting with `!`.
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """This triggers automatically once the bot successfully logs into Discord."""
    logger.info(f"Logged in as {bot.user} and ready to receive commands.")

# ==========================================
# 5. API FETCH FUNCTIONS
# ==========================================
# These functions use `aiohttp` to make asynchronous web requests. 
# Async prevents the bot from "freezing" while waiting for the web API to respond.

async def fetch_coordinates(city: str) -> dict | None:
    """
    Geocoding Step: 
    Takes a city string (e.g., "Paris") and asks the Open-Meteo Geocoding API 
    for the exact latitude, longitude, and local timezone.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            if "results" in data and len(data["results"]) > 0:
                return data["results"][0]  # Return the top match
            return None

async def fetch_weather_data(lat: float, lon: float, tz: str) -> dict:
    """
    Weather Step: 
    Takes the coordinates from `fetch_coordinates` and asks the Open-Meteo Forecast API
    for the current conditions and the next two days of daily maximums/minimums.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,daylight_duration,weather_code",
        "timezone": tz,
        "timeformat": "unixtime",
        "forecast_days": 2
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            return await response.json()

# ==========================================
# 6. DISCORD COMMAND DEFINITION
# ==========================================
# This registers the `!weather` command. If the user types `!weather London`, 
# the variable `city` becomes "London". If they type `!weather`, it defaults to "Warsaw".

@bot.command(name="weather", help="Get the current weather forecast")
async def weather(ctx: commands.Context, *, city: str = "Warsaw"):
    try:
        # Step A: Translate the city name into coordinates
        location = await fetch_coordinates(city)
        if not location:
            await ctx.send(f"❌ Could not find coordinates for `{city}`. Please check the spelling.")
            return

        loc_name = location.get("name")
        country = location.get("country", "")
        lat = location.get("latitude")
        lon = location.get("longitude")
        tz_str = location.get("timezone", "UTC")

        # Step B: Pass those exact coordinates to get the weather data
        data = await fetch_weather_data(lat, lon, tz_str) # type: ignore

        # Step C: Extract the "Current" conditions from the JSON response
        current = data['current']
        curr_temp = current['temperature_2m']
        curr_humidity = current['relative_humidity_2m']
        curr_code = format_weather_code(current['weather_code'])
        curr_time = format_unix_timestamp(current['time'], tz_str)

        # Step D: Extract the "Daily" forecast from the JSON response.
        # The API returns daily data as lists. Index [0] is today, [1] is tomorrow.
        daily = data['daily']
        
        today_max = daily['temperature_2m_max'][0]
        today_min = daily['temperature_2m_min'][0]
        today_precip = daily['precipitation_probability_max'][0]
        today_code = format_weather_code(daily['weather_code'][0])
        # Convert seconds of daylight into hours and minutes
        today_dl_hours = int(daily['daylight_duration'][0] // 3600)
        today_dl_mins = int((daily['daylight_duration'][0] % 3600) // 60)

        tom_max = daily['temperature_2m_max'][1]
        tom_min = daily['temperature_2m_min'][1]
        tom_precip = daily['precipitation_probability_max'][1]
        tom_code = format_weather_code(daily['weather_code'][1])
        tom_dl_hours = int(daily['daylight_duration'][1] // 3600)
        tom_dl_mins = int((daily['daylight_duration'][1] % 3600) // 60)

        # Step E: Construct the final string to send back to Discord
        weather_output = (
            "========================================\n"
            f"📍 **{loc_name}, {country}** | 🗓️ **{curr_time}**\n\n"
            f"**Current:** {curr_code} | 🌡️ **Temp:** {curr_temp:.1f}°C, 💧 **Humidity:** {curr_humidity:.0f}%\n\n"
            f"**Today's Forecast:** {today_code}\n"
            f"⬆️/⬇️ **Temp:** {today_max:.1f}°C/{today_min:.1f}°C\n"
            f"☔ **Precip. Prob:** {today_precip:.0f}% | ☀️ **Daylight:** {today_dl_hours}h {today_dl_mins}m\n\n"
            f"**Tomorrow's Forecast:** {tom_code}\n"
            f"⬆️/⬇️ **Temp:** {tom_max:.1f}°C/{tom_min:.1f}°C\n"
            f"☔ **Precip. Prob:** {tom_precip:.0f}% | ☀️ **Daylight:** {tom_dl_hours}h {tom_dl_mins}m\n"
            "======================================== v2"
        )

        # Step F: Send the formatted string back to the channel where the command was called
        await ctx.send(weather_output)
        logger.info(f"Weather forecast for {loc_name} sent to {ctx.author.name}.")
        
    except Exception as e:
        # Catch any network errors or data parsing errors so the bot doesn't crash
        logger.exception("An error occurred while fetching weather data:")
        await ctx.send(f"❌ An error occurred while fetching weather data. Error: `{e}`")

# ==========================================
# 7. EXECUTION
# ==========================================
# This block ensures the bot only runs if this file is executed directly 
# (not imported as a module elsewhere).
if __name__ == "__main__":
    bot.run(TOKEN)