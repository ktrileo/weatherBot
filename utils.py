# weatherbot/utils.py
import datetime
import logging
import pytz # For timezone conversions

logger = logging.getLogger('Utils')

def format_unix_timestamp(unix_timestamp: int, timezone_str: str) -> str:
    """
    Converts a Unix timestamp (seconds since epoch) to a human-readable string
    in a specified timezone.

    Args:
        unix_timestamp (int): The Unix timestamp in seconds.
        timezone_str (str): The IANA timezone string (e.g., "Europe/Warsaw").

    Returns:
        str: A formatted datetime string (e.g., "2025-07-23 18:05 CEST").
    """
    try:
        # Convert to UTC datetime object first for consistency and robustness
        dt_object_utc = datetime.datetime.fromtimestamp(unix_timestamp, tz=datetime.timezone.utc)

        # Get the target timezone object
        target_tz = pytz.timezone(timezone_str)

        # Convert UTC datetime to the target timezone
        dt_object_target_tz = dt_object_utc.astimezone(target_tz)

        # Format the datetime object into a readable string
        return dt_object_target_tz.strftime('%Y-%m-%d %H:%M %Z')
    except pytz.UnknownTimeZoneError:
        logger.error(f"Unknown timezone string provided: '{timezone_str}'. Falling back to UTC for formatting.")
        # Fallback to UTC if the specified timezone is invalid
        return datetime.datetime.fromtimestamp(unix_timestamp, tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    except Exception as e:
        logger.error(f"An unexpected error occurred while formatting timestamp {unix_timestamp}: {e}", exc_info=True)
        return f"Timestamp Error: {unix_timestamp}"

def format_weather_code(weather_code: float) -> str:
    wmo = {
            0.0 : 'Clear Sky',
            1.0 : 'Mainly clear',
            2.0 : 'Partly cloudy',
            3.0 : 'Overcast',
            45.0 : 'Foggy',
            46.0 : 'Rime fog',
            51.0 : 'Light drizzle',
            53.0 : 'Moderate drizzle',
            55.0 : 'Dense drizzle',
            56.0 : 'Light freezing drizzle',
            57.0 : 'Dense freezing drizzle',
            61.0 : 'Slight rain',
            63.0 : 'Moderate rain',
            65.0 : 'Heavy rain',
            71.0 : 'Slight snow fall',
            73.0 : 'Moderate snow fall',
            75.0 : 'Heavy snow fall',
            77.0 : 'Snow grains',
            80.0 : 'Slight rain showers',
            81.0 : 'Moderate rain showers',
            82.0 : 'Violent rain showers',
            85.0 : 'Slight snow showers',
            86.0 : 'Heavy snow showers',
            95.0 : 'Thunderstorms',
            96.0 : 'Thunderstorms with slight hail',
            99.0 : 'Thunderstorms with heavy hail'
        }
    try:
        # Direct lookup since dictionary keys are now floats, matching the input type hint
        description = wmo.get(weather_code, "Unknown weather code")
        
        if description == "Unknown weather code":
            logging.warning(f"Received unknown weather code: {weather_code}. Mapping not found.")
            
        return description
        
    except TypeError as e:
        # This might catch if weather_code isn't a number at all (e.g., a string)
        logging.error(f"TypeError with weather code '{weather_code}': {e}", exc_info=True)
        return f"Invalid code type: {weather_code}"
    except Exception as e:
        # Catch any other unexpected errors
        logging.error(f"An unexpected error occurred while getting the weather code value for '{weather_code}': {e}", exc_info=True)
        return f"Error processing code: {weather_code}"