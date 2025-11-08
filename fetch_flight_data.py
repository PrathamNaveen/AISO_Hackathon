'''
This script is used to fetch the flight data from the serpapi.com

'''

from serpapi import GoogleSearch
import json
from datetime import datetime, timedelta

user_information = {
  "date": "2025-12-10",
  "location": "Amsterdam",
  "departure_airport": "AMS",  # tbd
  "destination": "Austin",
  "arrival_airport": "AUS",  # tbd
  "days": 10,
  "budget": 1000
}

# convert the user_information to the params

params = {
  "engine": "google_flights",
  "departure_id": user_information['departure_airport'],         # Amsterdam Schiphol
  "arrival_id": user_information['arrival_airport'],           # New York JFK
  "outbound_date": user_information['date'],
  "return_date": (datetime.strptime(user_information['date'], '%Y-%m-%d') + timedelta(days=user_information['days'])).strftime('%Y-%m-%d'),
  "currency": "EUR",  # tbd
  "hl": "en",                    # language
  "api_key": "f20ff35e3dde89cba464ae5423dd93fb2a2aaecb6a41acf98fc3d9858906b6ef"
}
# print the params
print(params)
# parse the results to get the flight data
# # load the results from the json file

# # search the flight data
# search = GoogleSearch(params)
# results = search.get_dict()
# flight_data = results

with open('flight_data.json', 'r') as f:
    results = json.load(f)
flight_data = results

# pick top 3 flights, with information: airline, airport, price, duration, departure_time, arrival_time
top_3_flights_raw = flight_data['best_flights'][:3]

# Extract and format the flight information
top_3_flights = []
for flight in top_3_flights_raw:
    # Get the first flight segment (main outbound flight)
    first_segment = flight['flights'][0]
    
    flight_info = {
        "airline": first_segment['airline'],
        "departure_airport": first_segment['departure_airport']['name'],
        "arrival_airport": first_segment['arrival_airport']['name'],
        "price": flight['price'],
        "duration": flight['total_duration'],
        "departure_time": first_segment['departure_airport']['time'],
        "arrival_time": first_segment['arrival_airport']['time']
    }
    top_3_flights.append(flight_info)

# Convert to JSON and print
top_3_flights_json = json.dumps(top_3_flights, indent=2)
print(top_3_flights_json)

# # Optionally save to a file
# with open('top_3_flights.json', 'w') as f:
#     json.dump(top_3_flights, f, indent=2)
