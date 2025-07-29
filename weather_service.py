# weatherbot/weather_service.py
import logging

import openmeteo_requests
import requests_cache
from retry_requests import retry
import numpy as np # Used for .ValuesAsNumpy()

# Import configuration from the config module
import config

logger = logging.getLogger('WeatherService')

class WeatherService:
    """
    A service class to handle all interactions with the Open-Meteo API.
    It manages the API client, constructs requests, and extracts raw data.
    """
    def __init__(self, latitude: float, longitude: float, timezone: str):
        """
        Initializes the WeatherService with geographical and timezone settings.

        Args:
            latitude (float): The latitude for weather forecasts.
            longitude (float): The longitude for weather forecasts.
            timezone (str): The IANA timezone name for the API request.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.timezone = timezone

        # Setup requests-cache session for caching API responses
        # This helps reduce redundant API calls if data is requested frequently.
        cache_session = requests_cache.CachedSession(
            '.cache',
            expire_after=config.CACHE_EXPIRE_AFTER_SECONDS
        )
        # Setup retry mechanism for robustness against transient network issues
        retry_session = retry(
            cache_session,
            retries=config.RETRY_ATTEMPTS,
            backoff_factor=config.RETRY_BACKOFF_FACTOR
        )
        # Initialize the Open-Meteo client with the configured session
        self.client = openmeteo_requests.Client(session=retry_session)
        logger.info(f"WeatherService initialized for Lat: {latitude}, Lon: {longitude}, Timezone: {timezone}")

    async def fetch_weather_data(self) -> dict:
        """
        Fetches current and daily weather data from the Open-Meteo API.

        This method constructs the API request parameters using the configured
        variables and then calls the Open-Meteo API. It extracts the relevant
        current and daily data, ensuring scalar values are returned from NumPy arrays.

        Returns:
            dict: A dictionary containing 'current' and 'daily' weather data.
                  Example:
                  {
                      'current': {
                          'time': 1753285500,
                          'temperature_2m': 20.5,
                          # ... other current variables
                      },
                      'daily': {
                          'time': 1753285500,
                          'temperature_2m_max': 25.1,
                          # ... other daily variables
                      }
                  }
        Raises:
            Exception: If the API request fails, the response is malformed,
                       or data extraction encounters an issue.
        """
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": config.CURRENT_WEATHER_VARIABLES,
            "daily": config.DAILY_WEATHER_VARIABLES,
            "timezone": self.timezone,
            "forecast_days": config.FORECAST_DAYS,
            "timeformat": config.TIME_FORMAT
        }

        logger.info(f"Making Open-Meteo API request to {config.OPENMETEO_API_URL} with params: {params}")

        try:
            # The weather_api() call is an I/O operation and should be awaited.
            responses = self.client.weather_api(config.OPENMETEO_API_URL, params=params)
            response = responses[0] # Get the first (and only) response for the specified location

            # --- Extract Current Data ---
            current_data = {}
            current_raw = response.Current()
            current_data['time'] = current_raw.Time() # Unix timestamp for current time

            # Dynamically extract current variables based on config.CURRENT_WEATHER_VARIABLES
            for i, var_name in enumerate(config.CURRENT_WEATHER_VARIABLES):
                try:
                    current_data[var_name] = current_raw.Variables(i).Value()
                except IndexError:
                    logger.error(f"Current variable '{var_name}' at index {i} not found in API response. Check config.CURRENT_WEATHER_VARIABLES order.")
                    current_data[var_name] = None # Assign None or a default value if not found

            # --- Extract Daily Data ---
            daily_data = {}
            daily_raw = response.Daily()
            # Daily time is usually the start of the day in Unix timestamp
            daily_data['time'] = daily_raw.Time()

            # Dynamically extract daily variables based on config.DAILY_WEATHER_VARIABLES
            for i, var_name in enumerate(config.DAILY_WEATHER_VARIABLES):
                try:
                    # ValuesAsNumpy() returns a NumPy array; [0] extracts the scalar value for forecast_days=1
                    daily_data[var_name] = daily_raw.Variables(i).ValuesAsNumpy()[0]
                except IndexError:
                    logger.error(f"Daily variable '{var_name}' at index {i} not found in API response. Check config.DAILY_WEATHER_VARIABLES order.")
                    daily_data[var_name] = None # Assign None or a default value if not found

            logger.info("Successfully fetched and parsed weather data.")
            return {
                'current': current_data,
                'daily': daily_data
                }

        except Exception as e:
            # Log the full traceback for detailed error analysis in SRE context
            logger.error(f"Failed to fetch weather data from Open-Meteo API: {e}", exc_info=True)
            raise # Re-raise the exception to be handled by the caller (main.py)

