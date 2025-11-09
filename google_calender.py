from __future__ import print_function
import os.path
from datetime import datetime
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


def main():
    """Main function to get and display December 2025 events."""
    events = get_december_2025_events()
    print(events)
    return events


if __name__ == '__main__':
    main()
