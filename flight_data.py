from serpapi.google_search import GoogleSearch
from dotenv import load_dotenv
import os
import json
load_dotenv()

api_key = os.getenv("SERPAPI_API_KEY")

params = {
  "engine": "google_flights",
  "departure_id": "AMS", # departure airport code
  "arrival_id": "JFK", # arrival airport code
  "outbound_date": "2025-11-09", # outbound date
  "return_date": "2025-11-15", # return date
  "currency": "USD", # currency
  "hl": "en",
  "api_key": api_key,
  "sort_by": 1 # sort by top flights (defualt), or 2 for price
}

# retrieve only best flights
search = GoogleSearch(params)
# return result of the api call
results = search.get_dict()
# pretty json
pretty_json = json.loads(json.dumps(results, indent=4))
with open("flight_data.json", "w") as f:
    json.dump(pretty_json, f, indent=4)
print(pretty_json)