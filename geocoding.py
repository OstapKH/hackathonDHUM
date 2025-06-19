from functools import lru_cache
from geopy.geocoders import Nominatim
import logging
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize geolocator
geolocator = Nominatim(user_agent="plu_g2_app", timeout=10)

@lru_cache(maxsize=None)  # Use LRU cache for in-memory caching
def get_city_coords(city_name):
    """
    Geocode a city name to get its latitude and longitude.
    Returns (lat, lon) or None if not found.
    Uses LRU cache to avoid repeated requests for the same city.
    """
    if not city_name or pd.isna(city_name) or city_name.lower() in ['s.l.', 'б.м.']:
        return None
    
    try:
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            logger.warning(f"Could not geocode city: {city_name}")
            return None
    except Exception as e:
        logger.error(f"Geocoding error for '{city_name}': {e}")
        return None 