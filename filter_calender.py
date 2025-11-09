from __future__ import print_function
import os.path
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
# ignore the warning
import warnings
warnings.filterwarnings('ignore')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_december_2025_events():
    """
    Get all events from Google Calendar in December 2025.
    
    Returns:
        list: List of calendar events in December 2025
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Set time range for December 2025
    time_min = '2025-12-01T00:00:00Z'  # December 1, 2025, 00:00:00 UTC
    time_max = '2026-01-01T00:00:00Z'  # January 1, 2026, 00:00:00 UTC (end of December)

    # Call the Calendar API for December 2025 events
    print('📅 Getting events in December 2025...')
    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    if not events:
        print('❌ No events found in December 2025.')
        return []
    
    print(f'✅ Found {len(events)} events in December 2025:\n')
    for i, event in enumerate(events, 1):
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        summary = event.get('summary', 'No Title')
        location = event.get('location', 'No Location')
        
        print(f"{i}. {summary}")
        print(f"📍 {location}")
        print(f"🕐 Start: {start}")
        print(f"🕐 End: {end}")
        print()
    # return just the summary, location, and the start and end time
    events_data = []
    for event in events:
        events_data.append({
            "summary": event.get('summary', 'No Title'),
            "location": event.get('location', 'No Location'),
            "start": event.get('start', 'No Start'),
            "end": event.get('end', 'No End')
        })
    return events_data


def _parse_event_time(value):
    """
    Convert a Google Calendar event time representation into a datetime object.

    Args:
        value (dict|str): Event time data (may include dateTime/date keys).

    Returns:
        tuple[datetime|None, bool]: Parsed datetime (or None) and flag indicating all-day event.
    """
    if not value:
        return None, False

    raw = value
    all_day = False

    if isinstance(value, dict):
        raw = value.get('dateTime')
        if raw:
            all_day = False
        else:
            raw = value.get('date')
            all_day = True
    elif isinstance(value, str):
        raw = value
        all_day = len(value) == 10  # YYYY-MM-DD format indicates all-day

    if not raw:
        return None, False

    normalized = raw.replace('Z', '+00:00')

    try:
        if all_day:
            parsed = datetime.strptime(normalized[:10], '%Y-%m-%d')
        else:
            parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed = datetime.strptime(normalized[:10], '%Y-%m-%d')
            all_day = True
        except ValueError:
            return None, False

    return parsed, all_day


def _parse_flight_date(date_str):
    """
    Parse a flight date string into a datetime object.

    Args:
        date_str (str): Date string in YYYY-MM-DD or ISO format.

    Returns:
        datetime|None: Parsed datetime object (date component only).
    """
    if not date_str:
        return None

    normalized = date_str.replace('Z', '+00:00')

    for parser in (
        lambda val: datetime.strptime(val[:10], '%Y-%m-%d'),
        lambda val: datetime.fromisoformat(val)
    ):
        try:
            return parser(normalized)
        except ValueError:
            continue

    return None

def get_flights():
    from message import fetch_flight_data_from_serpapi
    flights = fetch_flight_data_from_serpapi(
        departure_id="AMS",
        arrival_id="ATL",
        outbound_date="2025-12-25",
        return_date="2025-12-25",
        currency="EUR",
        sort_by=1,
        parse_only_essentials=True
    )
    print(flights)
    return flights
# filter the flights which not conflicts with the event start and end time
def filter_flights(events, flights):
    # filter the flights which not conflicts with the event start and end time
    filtered_flights = []
    for flight in flights:
        departure_dt = _parse_flight_date(flight.get('departure_date'))
        return_dt = _parse_flight_date(flight.get('return_date'))

        if not departure_dt or not return_dt:
            print(f"⚠️ Skipping flight {flight.get('airline', 'Unknown')} due to invalid dates.")
            continue

        flight_start = departure_dt.date()
        flight_end = return_dt.date()

        conflicts = False

        for event in events:
            event_start_raw = event.get('start')
            event_end_raw = event.get('end')

            event_start_dt, start_all_day = _parse_event_time(event_start_raw)
            event_end_dt, end_all_day = _parse_event_time(event_end_raw)

            if not event_start_dt or not event_end_dt:
                continue

            event_start_date = event_start_dt.date()
            event_end_date = event_end_dt.date()

            # Google Calendar all-day events use exclusive end date; adjust to inclusive range.
            if start_all_day or end_all_day:
                event_end_date = (event_end_dt - timedelta(days=1)).date()

            overlaps = flight_start <= event_end_date and flight_end >= event_start_date

            if overlaps:
                conflicts = True
                print(f"❌ Flight {flight['airline']} conflicts with event {event['summary']} ({event_start_raw} → {event_end_raw})")
                break

        if not conflicts:
            filtered_flights.append(flight)
            print(f"✅ Flight {flight['airline']} does not conflict with any events.")
    return filtered_flights

def main():
    """Main function to get and display December 2025 events."""
    events = get_december_2025_events()
    flights = get_flights()
    filtered_flights = filter_flights(events, flights)
    print("Filtered flights:")
    print(filtered_flights)
    return filtered_flights


if __name__ == '__main__':
    main()
