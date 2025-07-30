# weatherbot/main.py
import os
import sys
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Import modules from your project
import config
from weather_service import WeatherService
from utils import format_unix_timestamp
from utils import format_weather_code

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('MainBot')

# --- Load Environment Variables ---
load_dotenv() # Load from .env file for local development

# --- Validate Environment Variables ---
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_NAME = os.getenv('DISCORD_GUILD_NAME')

if not TOKEN:
    logger.critical("DISCORD_BOT_TOKEN environment variable not set. Exiting.")
    sys.exit(1)
if not GUILD_NAME:
    logger.warning("DISCORD_GUILD_NAME environment variable not set. Bot will connect but might not find a specific guild by name.")

# --- Discord Bot Intents ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# --- Discord Client Initialization ---
# Using commands.Bot is generally recommended for bots with commands.
# If you stick with discord.Client, ensure on_message handles all parsing.
bot = commands.Bot(command_prefix=config.COMMAND_PREFIX, intents=intents)

# --- Initialize Services ---
# Pass configuration parameters to the service classes
weather_service = WeatherService(
    latitude=config.DEFAULT_LATITUDE,
    longitude=config.DEFAULT_LONGITUDE,
    timezone=config.OPENMETEO_API_TIMEZONE
)

# --- Global API Call Counter ---
api_call_count: int = 0

# --- Discord Event Handlers ---

@bot.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    logger.info(f'{bot.user} has connected to Discord! (ID: {bot.user.id})')
    logger.info(f'Bot is ready to receive commands with prefix: "{config.COMMAND_PREFIX}"')

    target_guild: discord.Guild | None = None
    for guild in bot.guilds:
        if guild.name == GUILD_NAME:
            target_guild = guild
            break

    if target_guild:
        logger.info(f'Bot found target guild: {target_guild.name} (ID: {target_guild.id})')
    else:
        logger.warning(f'Bot is not connected to a guild named: "{GUILD_NAME}". Check GUILD_NAME in .env.')
        logger.info(f'Connected to the following guilds: {[g.name for g in bot.guilds]}')

@bot.command(name='weather')
async def get_weather(ctx: commands.Context):
    """
    Fetches and displays current weather and today's forecast for Warsaw, Poland.
    Usage: !weather
    """
    global api_call_count
    api_call_count += 1 # Increment counter for each API call attempt

    logger.info(f"'{ctx.author}' requested weather. API call count: {api_call_count}")

    try:
        # Fetch weather data using the dedicated service
        weather_data = await weather_service.fetch_weather_data()

        # Extract and format data
        current_temp = weather_data['current']['temperature_2m']
        current_humidity = weather_data['current']['relative_humidity_2m']
        current_weather_code = weather_data['current']['weather_code']

        # Accessing the first element of 'daily' lists for forecast data
        daily_max_temp = weather_data['daily']['temperature_2m_max']
        daily_min_temp = weather_data['daily']['temperature_2m_min']
        daily_precip_prob = weather_data['daily']['precipitation_probability_max']
        daily_daylight_duration_sec = weather_data['daily']['daylight_duration']
        daily_weather_code = weather_data['daily']['weather_code']

        daylight_hours = int(daily_daylight_duration_sec // 3600)
        daylight_minutes = int((daily_daylight_duration_sec % 3600) // 60)

        # Extract and format tomorrow's data (index 1)
        tomorrow_max_temp = weather_data['tomorrow']['temperature_2m_max']
        tomorrow_min_temp = weather_data['tomorrow']['temperature_2m_min']
        tomorrow_precip_prob = weather_data['tomorrow']['precipitation_probability_max']
        tomorrow_daylight_duration_sec = weather_data['tomorrow']['daylight_duration']
        tomorrow_weather_code = weather_data['tomorrow']['weather_code']

        tomorrow_daylight_hours = int(tomorrow_daylight_duration_sec // 3600)
        tomorrow_daylight_minutes = int((tomorrow_daylight_duration_sec % 3600) // 60)


        formatted_current_time = format_unix_timestamp(
            weather_data['current']['time'],
            timezone_str=config.DISPLAY_TIMEZONE
        )

        formatted_weather_code_current = format_weather_code(current_weather_code)
        formatted_weather_code_daily = format_weather_code(daily_weather_code)
        formatted_weather_code_tomorrow = format_weather_code(tomorrow_weather_code)

        # Construct the human-readable output message (small and informative)
        weather_output = (
            f"📍 **Weather in Warsaw, Poland**\n"
            f"🗓️ **As of:** {formatted_current_time}\n\n"
            f"**Current Conditions:**\n"
            f"  🌡️ Temp: {current_temp:.1f}°C\n"
            f"  💧 Humidity: {current_humidity:.0f}%\n"
            f"  ☁️ Conditions: {formatted_weather_code_current}\n\n"
            f"**Today's Forecast:**\n"
            f"  ⬆️ Max Temp: {daily_max_temp:.1f}°C\n"
            f"  ⬇️ Min Temp: {daily_min_temp:.1f}°C\n"
            f"  ☔ Precip. Prob: {daily_precip_prob:.0f}%\n"
            f"  ☀️ Daylight: {daylight_hours}h {daylight_minutes}m\n"
            f"  🌦️ Conditions: {formatted_weather_code_daily}\n\n" # Added an extra newline here

            f"**🗓️ Tomorrow's Forecast:**\n" # New section header
            f"  ⬆️ Max Temp: {tomorrow_max_temp:.1f}°C\n"
            f"  ⬇️ Min Temp: {tomorrow_min_temp:.1f}°C\n"
            f"  ☔ Precip. Prob: {tomorrow_precip_prob:.0f}%\n"
            f"  ☀️ Daylight: {tomorrow_daylight_hours}h {tomorrow_daylight_minutes}m\n"
            f"  🌦️ Conditions: {formatted_weather_code_tomorrow}\n"
        )

        # Send the message to the command channel
        await ctx.send(weather_output)
        # Determine channel name for logging based on channel type
        ctx_channel_name_for_log = ctx.channel.name if isinstance(ctx.channel, discord.TextChannel) else "DM"
        logger.info(f"Weather forecast sent to channel: {ctx_channel_name_for_log} (ID: {ctx.channel.id})")

        
        # Send the message to the command channel
        #await ctx.send(weather_output)
        #logger.info(f"Weather forecast sent to channel: {ctx.channel.name} (ID: {ctx.channel.id})")

    except Exception as e:
        logger.exception(f"An error occurred while fetching or processing weather data for '{ctx.author}':")
        await ctx.send(f"An error occurred while fetching weather data. Please try again later. Error: `{e}`")

@bot.command(name='apicount')
async def show_api_count(ctx: commands.Context):
    """
    Displays the current count of API calls made by the bot.
    Usage: !apicount
    """
    await ctx.send(f"The weather API has been called `{api_call_count}` times since the bot started.")
    logger.info(f"'{ctx.author}' requested API call count: {api_call_count}")

# --- Run the Bot ---
if __name__ == "__main__":
    logger.info("Starting Discord bot...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.critical("Failed to log in. Invalid bot token provided.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred while running the bot: {e}", exc_info=True)

