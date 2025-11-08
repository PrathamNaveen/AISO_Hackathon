'''
This script is used to fetch the flight data from the serpapi.com

'''

from serpapi import GoogleSearch
import json
from datetime import datetime, timedelta
import os


def fetch_flight_data_from_api(preferences=None):
    """
    Fetch top 3 flight data from SerpAPI or cached JSON file.
    
    Args:
        preferences (dict): User preferences including:
            - departure_airport (str): Departure airport code
            - arrival_airport (str): Arrival airport code
            - date (str): Departure date in YYYY-MM-DD format
            - days (int): Number of days for the trip
            - budget (int): Maximum budget
            - use_live_api (bool): Whether to use live API or cached data
    
    Returns:
        list: Top 3 flights with airline, price, duration, and route information
    """
    # Default preferences
    default_prefs = {
        "date": "2025-12-25",
        "departure_airport": "AMS",
        "arrival_airport": "ATL",
        "days": 10,
        "budget": 1000,
        "use_live_api": True
    }
    
    # Merge with user preferences
    if preferences:
        default_prefs.update(preferences)
    prefs = default_prefs
    
    # Get flight data (from cache or API)
    if prefs.get("use_live_api", False):
        flight_data = _fetch_from_api(prefs)
    else:
        flight_data = _load_from_cache()
    
    if not flight_data or 'best_flights' not in flight_data:
        return []
    
    # Extract top 3 flights
    flights_raw = flight_data['best_flights']
    
    # Format the flight information
    all_flights = []
    for flight in flights_raw:
        # Get the first flight segment (main outbound flight)
        first_segment = flight['flights'][0]
        
        # Convert duration from minutes to hours format
        duration_minutes = flight['total_duration']
        duration_hours = duration_minutes // 60
        duration_mins = duration_minutes % 60
        duration_str = f"{duration_hours}h {duration_mins}m" if duration_mins > 0 else f"{duration_hours}h"
        
        # Create route string
        dep_code = first_segment['departure_airport']['id']
        arr_code = first_segment['arrival_airport']['id']
        route = f"{dep_code} → {arr_code}"
        
        flight_info = {
            "airline": first_segment['airline'],
            "price": flight['price'],
            "duration": duration_str,
            "route": route,
            "departure_airport": first_segment['departure_airport']['name'],
            "arrival_airport": first_segment['arrival_airport']['name'],
            "departure_time": first_segment['departure_airport']['time'],
            "arrival_time": first_segment['arrival_airport']['time']
        }
        all_flights.append(flight_info)
    
    return all_flights


def _fetch_from_api(preferences):
    """Fetch flight data from SerpAPI (live API call)"""
    params = {
        "engine": "google_flights",
        "departure_id": preferences['departure_airport'],
        "arrival_id": preferences['arrival_airport'],
        "outbound_date": preferences['date'],
        "return_date": (datetime.strptime(preferences['date'], '%Y-%m-%d') + 
                       timedelta(days=preferences['days'])).strftime('%Y-%m-%d'),
        "currency": "EUR",
        "hl": "en",
        "api_key": os.getenv("SERPAPI_KEY", "f20ff35e3dde89cba464ae5423dd93fb2a2aaecb6a41acf98fc3d9858906b6ef")
    }
    
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        return results
    except Exception as e:
        print(f"❌ Error fetching from API: {e}")
        return _load_from_cache()


def _load_from_cache():
    """Load flight data from cached JSON file"""
    cache_file = os.path.join(os.path.dirname(__file__), 'flight_data.json')
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Cache file not found: {cache_file}")
        return None


# For testing when run directly
if __name__ == "__main__":
    print("🔍 Testing flight data fetching...\n")
    
    # Test with default preferences
    flights = fetch_flight_data_from_api()
    
    print("✈️ Top 3 Flights:")
    # print(json.dumps(flights, indent=2))
    
    
    # Optionally save to a file
    # with open('top_3_flights.json', 'w') as f:
    #     json.dump(flights, f, indent=2)
    # print("\n✅ Saved to top_3_flights.json")
