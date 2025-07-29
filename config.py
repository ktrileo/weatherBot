# weatherbot/config.py

# --- Discord Bot Configuration ---
COMMAND_PREFIX = '!' # The prefix for bot commands (e.g., !weather)

# --- Open-Meteo API Configuration ---
OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"

# Default geographical coordinates for weather forecasts (Used location: Warsaw, Poland)
DEFAULT_LATITUDE = 52.2298
DEFAULT_LONGITUDE = 21.0118

# Timezone used for the Open-Meteo API request (IANA format).
# Europe/Berlin covers Warsaw for API requests.
OPENMETEO_API_TIMEZONE = "Europe/Berlin"

# Timezone used for displaying human-readable timestamps in the bot's output.
# This is specifically for user-facing messages.
DISPLAY_TIMEZONE = "Europe/Warsaw"

# --- API Request Parameters ---
# These lists define the specific weather variables requested from Open-Meteo.
# The order here is crucial as it determines the index for accessing values in the response.
CURRENT_WEATHER_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "weather_code",

]

DAILY_WEATHER_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_probability_max",
    "daylight_duration",
    "weather_code"
]

# Number of forecast days to request (1 for today's forecast)
FORECAST_DAYS = 2

# Time format for API response (unixtime is good for programmatic handling)
TIME_FORMAT = "unixtime"

# --- API Client Caching and Retry Settings ---
# Cache duration for API responses in seconds (e.g., 300 seconds = 5 minutes).
# Adjust based on how frequently you need fresh data vs. Open-Meteo's update cycle.
CACHE_EXPIRE_AFTER_SECONDS = 300

# Number of times to retry a failed API request
RETRY_ATTEMPTS = 5

# Factor for exponential backoff between retry attempts
RETRY_BACKOFF_FACTOR = 0.2