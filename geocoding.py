from functools import lru_cache
from geopy.geocoders import Nominatim
import logging
import pandas as pd
import os
import csv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- City Name Normalization ---
CITY_NAME_MAPPING = {
    "Екатеринослав": "Дніпро",  # Historical name for Dnipro
    "Катеринослав": "Дніпро",
    "б.м.": "",          # "без місця" (no place)
    "s.l.": "",          # "sine loco" (no place)
    "S.L.": "",
    "B.M.": "",
    "Б. м.": "",
    "Б.м": "",
    "Прага": "Prague",      # Use English names that geocoders prefer
    "Варшава": "Warsaw",
    "Львів": "Lviv",
    "Київ": "Kyiv",
    "Харків": "Kharkiv",
    "Петербург": "Saint Petersburg",
    "C.-Петербургъ": "Saint Petersburg",
    "Петроград": "Saint Petersburg",
    "Москва": "Moscow",
    "New-York": "New York",
    "Regensburg-Berchtesgaden": "Regensburg", # Handle multi-part names
    "Кремінчук": "Кременчук", # Typo correction
    "Тарнопіль": "Тернопіль", # Typo correction
    "Київ-Херсон": "" # Ambiguous, ignore
}

# --- Pre-computed Coordinates Cache ---
COORDS_CACHE_FILE = 'city_coordinates.csv'
_city_coords_cache = {}

def load_precomputed_coords():
    """Load coordinates from the pre-computed CSV file into memory."""
    if not os.path.exists(COORDS_CACHE_FILE):
        logger.warning(f"Coordinates cache file not found: {COORDS_CACHE_FILE}. App will run slower.")
        return

    try:
        with open(COORDS_CACHE_FILE, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)  # Skip header
            for row in reader:
                city, lat, lon = row
                _city_coords_cache[city] = (float(lat), float(lon))
        logger.info(f"Loaded {_city_coords_cache.__len__()} pre-computed city coordinates.")
    except Exception as e:
        logger.error(f"Error loading coordinates cache: {e}")

# Load the cache on module import
load_precomputed_coords()

# Initialize geolocator
geolocator = Nominatim(user_agent="plu_g2_app", timeout=10)

@lru_cache(maxsize=2048)  # Increase cache size for the session
def get_city_coords(city_name):
    """
    Geocode a city name to get its latitude and longitude.
    Uses a multi-level cache for performance.
    1. Normalizes the city name.
    2. Checks in-memory cache from pre-computed file.
    3. Falls back to geopy API call for unknown cities.
    """
    if not city_name or pd.isna(city_name):
        return None
    
    # 1. Normalize name
    normalized_city = CITY_NAME_MAPPING.get(city_name, city_name).strip()
    if not normalized_city:
        return None

    # 2. Check pre-computed cache
    if normalized_city in _city_coords_cache:
        return _city_coords_cache[normalized_city]

    # 3. Fallback to geocoding API
    try:
        location = geolocator.geocode(normalized_city)
        if location:
            coords = (location.latitude, location.longitude)
            _city_coords_cache[normalized_city] = coords # Cache for this session
            return coords
        else:
            _city_coords_cache[normalized_city] = None # Cache failure to avoid re-querying
            logger.warning(f"Could not geocode city: {city_name} (normalized to: {normalized_city})")
            return None
    except Exception as e:
        logger.error(f"Geocoding error for '{normalized_city}': {e}")
        return None 
