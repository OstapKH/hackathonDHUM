from functools import lru_cache
from geopy.geocoders import Nominatim
import logging
import pandas as pd
import os
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- City Name Normalization ---
CITY_NAME_MAPPING = {
    "Екатеринослав": "Дніпро",
    "Катеринослав": "Дніпро",
    "б.м.": "",          # "без місця" (no place)
    "s.l.": "",          # "sine loco" (no place)
    "S.L.": "",
    "B.M.": "",
    "Б. м.": "",
    "Б.м": "",
    "Прага": "Prague",
    "Варшава": "Warsaw",
    "Львів": "Lviv",
    "Київ": "Kyiv",
    "Харків": "Kharkiv",
    "Петербург": "Saint Petersburg",
    "C.-Петербургъ": "Saint Petersburg",
    "Петроград": "Saint Petersburg",
    "Москва": "Moscow",
    "New-York": "New York",
    "Regensburg-Berchtesgaden": "Regensburg",
    "Кремінчук": "Кременчук",
    "Тарнопіль": "Тернопіль",
    "Київ-Херсон": ""
}

COORDS_CACHE_FILE = 'data/city_coordinates.csv'
_city_coords_cache = {}

def load_precomputed_coords():
    """Load coordinates from the pre-computed CSV file into memory."""
    if not os.path.exists(COORDS_CACHE_FILE):
        logger.warning(f"Coordinates cache file not found: {COORDS_CACHE_FILE}. App will run slower.")
        return

    try:
        with open(COORDS_CACHE_FILE, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            next(reader)
            for row in reader:
                city, lat, lon = row
                _city_coords_cache[city] = (float(lat), float(lon))
    except Exception as e:
        logger.error(f"Error loading coordinates cache: {e}")

load_precomputed_coords()

geolocator = Nominatim(user_agent="plu_g2_app", timeout=10)

@lru_cache(maxsize=2048)
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
    
    normalized_city = CITY_NAME_MAPPING.get(city_name, city_name).strip()
    if not normalized_city:
        return None

    if normalized_city in _city_coords_cache:
        return _city_coords_cache[normalized_city]

    try:
        location = geolocator.geocode(normalized_city)
        if location:
            coords = (location.latitude, location.longitude)
            _city_coords_cache[normalized_city] = coords
            return coords
        else:
            _city_coords_cache[normalized_city] = None
            logger.warning(f"Could not geocode city: {city_name} (normalized to: {normalized_city})")
            return None
    except Exception as e:
        logger.error(f"Geocoding error for '{normalized_city}': {e}")
        return None 
