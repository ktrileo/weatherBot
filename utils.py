# your_bot_project/utils.py
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

