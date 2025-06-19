import pandas as pd
from geocoding import get_city_coords, CITY_NAME_MAPPING
import logging
import time
import csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_FILE = 'city_coordinates.csv'

def precompute_city_coordinates():
    """
    Pre-computes coordinates for all unique cities in the metadata
    and saves them to a CSV file. This script needs to be run only once.
    """
    logger.info("Starting geocode pre-computation...")
    
    # Load metadata
    try:
        df = pd.read_csv('PluG2_metadata.psv', sep='|', low_memory=False)
        logger.info(f"Loaded {len(df)} records from metadata file.")
    except Exception as e:
        logger.error(f"Could not load metadata file 'PluG2_metadata.psv': {e}")
        return

    # Get unique, non-empty city names
    unique_cities = df['Publication City'].dropna().unique()
    unique_cities = [city for city in unique_cities if str(city).strip()]
    logger.info(f"Found {len(unique_cities)} unique city names to process.")

    results = {}
    processed_count = 0
    start_time = time.time()

    for city in unique_cities:
        # Normalize the name first, as in the real function
        normalized_city = CITY_NAME_MAPPING.get(city, city).strip()
        
        if not normalized_city or normalized_city in results:
            continue # Skip empty or already processed names
        
        # This will use the full caching logic from the updated geocoding.py
        coords = get_city_coords(normalized_city)
        results[normalized_city] = coords
        
        processed_count += 1
        if processed_count % 20 == 0:
            logger.info(f"Processed {processed_count}/{len(unique_cities)} cities...")
        
        # Add a delay to not overwhelm the Nominatim API
        # Nominatim usage policy requires max 1 request/second
        time.sleep(1.1) 

    end_time = time.time()
    logger.info(f"Geocoding finished in {end_time - start_time:.2f} seconds.")
    
    # Write results to CSV
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['city', 'latitude', 'longitude'])
            
            valid_coords_count = 0
            for city, coords in results.items():
                if coords:
                    writer.writerow([city, coords[0], coords[1]])
                    valid_coords_count += 1
        
        logger.info(f"Successfully wrote {valid_coords_count} valid coordinates to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    precompute_city_coordinates() 
