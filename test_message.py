#!/usr/bin/env python3
"""
Test script for the updated message.py with parsing functionality
"""

from message import fetch_flight_data_from_serpapi
import json

print("=" * 60)
print("Testing message.py - Flight Data Parsing")
print("=" * 60)

# Test with parse_only_essentials=True (default)
print("\n📋 Test 1: Fetching and parsing essential attributes...")
try:
    parsed_flights = fetch_flight_data_from_serpapi(
        departure_id="AMS",
        arrival_id="ATL",
        outbound_date="2025-12-25",
        return_date="2026-01-04",
        currency="USD",
        sort_by=1,
        parse_only_essentials=True
    )
    
    print(f"\n✅ Successfully parsed {len(parsed_flights)} flights")
    print("\n🔝 Top 3 Flights:")
    for i, flight in enumerate(parsed_flights, 1):
        print(f"\n{i}. {flight['airline']} - ${flight['price']}")
        print(f"   📍 Route: {flight['route']}")
        print(f"   ⏱️  Duration: {flight['duration']}")
        print(f"   🛫 Departure: {flight['departure_time']}")
        print(f"   🛬 Arrival: {flight['arrival_time']}")
    
    # Save to file
    with open('test_parsed_flights.json', 'w', encoding='utf-8') as f:
        json.dump(parsed_flights, f, indent=2, ensure_ascii=False)
    print("\n💾 Saved top 3 to test_parsed_flights.json")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)

