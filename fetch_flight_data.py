from serpapi.google_search import GoogleSearch
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
# api_key = os.getenv("SERPAPI_API_KEY")
api_key = "f20ff35e3dde89cba464ae5423dd93fb2a2aaecb6a41acf98fc3d9858906b6ef"


def _parse_flight_data(flights_raw):
    """
    Parse raw flight data and extract essential attributes.
    
    Args:
        flights_raw (list): Raw flight data from SerpAPI
        
    Returns:
        list: Parsed flights with essential attributes only
    """
    parsed_flights = []
    
    for flight in flights_raw:
        # Get the first flight segment (main outbound flight)
        first_segment = flight['flights'][0]
        
        # Convert duration from minutes to hours format
        duration_minutes = flight.get('total_duration', 0)
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
            "arrival_time": first_segment['arrival_airport']['time'],
            "carbon_emissions": flight.get('carbon_emissions', {}),
            "airline_logo": first_segment.get('airline_logo', '')
        }
        parsed_flights.append(flight_info)
    
    
    return parsed_flights


def fetch_flight_data_from_serpapi(
    departure_id: str,
    arrival_id: str,
    outbound_date: str,
    return_date: str,
    currency: str,
    sort_by: int,
    parse_only_essentials: bool,
    output_file: str = None
):
    """
    Fetch flight data from SerpApi Google Flights and optionally parse essential attributes.

    Args:
        departure_id (str): IATA code of the departure airport (e.g., "AMS").
        arrival_id (str): IATA code of the arrival airport (e.g., "JFK").
        outbound_date (str): Outbound flight date in YYYY-MM-DD format.
        return_date (str): Return flight date in YYYY-MM-DD format.
        currency (str, optional): Currency code (default: "USD").
        sort_by (int, optional): Sorting method (1 = best flights, 2 = price).
        output_file (str, optional): File name for saving results.
        parse_only_essentials (bool, optional): If True, returns only essential attributes (default: True).

    Returns:
        list or dict: If parse_only_essentials=True, returns list of parsed flights.
                      Otherwise, returns full JSON response from SerpApi.
    """
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": currency,
        "hl": "en",
        "api_key": api_key,
        "sort_by": sort_by,
    }

    print(f"🔍 Fetching flights {departure_id} → {arrival_id} ({outbound_date} → {return_date})...")

    # Perform the API request
    search = GoogleSearch(params)
    results = search.get_dict()

    # Extract best_flights and other_flights from the response
    best_flights = results.get("best_flights", [])
    other_flights = results.get("other_flights", [])
    all_flights = best_flights + other_flights



    print(f"✈️ Found {len(all_flights)} flights.")
    
    # Parse and return essential attributes if requested
    if parse_only_essentials:
        parsed_flights = []
        for flight in all_flights:
            try:
                parsed_flights.append({
                    "airline": flight.get("airline", "Unknown"),
                    "price": flight.get("price", {}).get("amount") if isinstance(flight.get("price"), dict) else flight.get("price"),
                    "currency": currency,
                    "duration": flight.get("total_duration") or flight.get("duration"),
                    "route": f"{departure_id} → {arrival_id}",
                    "departure": departure_id,
                    "arrival": arrival_id,
                    "departure_date": outbound_date,
                    "return_date": return_date
                })
            except Exception as e:
                print(f"⚠️ Skipping invalid flight entry: {e}")
        print(f"✈️ Parsed {len(parsed_flights)} flights with essential attributes.")
        return parsed_flights


# Example usage:
if __name__ == "__main__":
    # Fetch and parse flight data (returns list of flights with essential attributes)
    parsed_flights = fetch_flight_data_from_serpapi(
        departure_id="AMS",
        arrival_id="ATL",
        outbound_date="2025-11-09",
        return_date="2025-11-15",
        currency="USD",
        sort_by=1,
        parse_only_essentials=True
    )
    
    print("\n✈️ Parsed Flight Data (Top 3):")
    for i, flight in enumerate(parsed_flights, 1):
        print(f"\n{i}. {flight['airline']} - ${flight['price']}")
        print(f"   Route: {flight['route']}")
        print(f"   Duration: {flight['duration']}")
        print(f"   Departure: {flight['departure_time']}")
        print(f"   Arrival: {flight['arrival_time']}")
    
    # Optionally save parsed data
    with open('parsed_flights.json', 'w', encoding='utf-8') as f:
        json.dump(parsed_flights, f, indent=2, ensure_ascii=False)
    print("\n✅ Parsed top 3 flights saved to parsed_flights.json")