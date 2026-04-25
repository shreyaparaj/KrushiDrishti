import os
import csv

# Path to the local CSV dataset.
CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'maharashtra_weather.csv')

def get_region_weather(region_name):
    """
    Reads from the local dataset data/maharashtra_weather.csv to fetch
    the temperature and rainfall of the given region.
    """
    default_weather = {"temp": 27.0, "rain": 900.0}
    
    if not os.path.exists(CSV_PATH):
        print(f"Dataset not found at {CSV_PATH}. Using defaults.")
        return default_weather

    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['district'].strip().lower() == region_name.strip().lower():
                    return {
                        "temp": float(row['avg_temp']),
                        "rain": float(row['avg_rainfall'])
                    }
    except Exception as e:
        print(f"Error reading {CSV_PATH}: {e}")
        
    # Fallback if the district wasn't in the CSV or an error occurred.
    print(f"Region '{region_name}' not found in dataset. Using defaults.")
    return default_weather
