"""
Gmail Email Access using OAuth2 (Client ID and Client Secret)

IMPORTANT: Redirect URI Setup
Before running this script, you MUST register the redirect URI in Google Cloud Console:
1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Navigate to "APIs & Services" > "Credentials"
3. Click on your OAuth 2.0 Client ID
4. Under "Authorized redirect URIs", add: http://localhost:8080
5. Save the changes

Setup Instructions:
1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a project or select existing one
3. Enable Gmail API
4. Go to "APIs & Services" > "Credentials"
5. Create OAuth 2.0 Client ID (Desktop application)
6. Add redirect URI: http://localhost:8080 (IMPORTANT!)
7. Download the credentials JSON file
8. Save as credentials.json in this directory
"""

import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
NUM_EMAILS = 10  # Number of recent emails to fetch
REDIRECT_PORT = 8080  # Fixed port for OAuth redirect (must match Google Cloud Console)

# Option 1: Use credentials.json file (download from Google Cloud Console)
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Option 2: Or set client_id and client_secret directly (alternative to credentials.json)
CLIENT_ID = os.getenv('GMAIL_CLIENT_ID', '')
CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET', '')

def get_credentials():
    """Get valid user credentials from storage or OAuth flow"""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Try to use credentials.json file first
            if os.path.exists(CREDENTIALS_FILE):
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                # Use fixed port that matches registered redirect URI in Google Cloud Console
                creds = flow.run_local_server(port=REDIRECT_PORT)
            # Otherwise, use client_id and client_secret from environment/config
            elif CLIENT_ID and CLIENT_SECRET:
                from google_auth_oauthlib.flow import Flow
                
                redirect_uri = f'http://localhost:{REDIRECT_PORT}'
                flow = Flow.from_client_config(
                    {
                        "installed": {
                            "client_id": CLIENT_ID,
                            "client_secret": CLIENT_SECRET,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                            "redirect_uris": [redirect_uri]
                        }
                    },
                    SCOPES
                )
                flow.redirect_uri = redirect_uri
                auth_url, _ = flow.authorization_url(prompt='consent')
                print(f'Please visit this URL to authorize the application: {auth_url}')
                code = input('Enter the authorization code: ')
                flow.fetch_token(code=code)
                creds = flow.credentials
            else:
                raise FileNotFoundError(
                    f"Either {CREDENTIALS_FILE} file not found, or CLIENT_ID and CLIENT_SECRET "
                    "not set. Please download credentials from Google Cloud Console."
                )
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds

def get_gmail_service():
    """Build and return Gmail service"""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)
    return service

def extract_email_body(payload):
    """Extract email body text from payload"""
    body = ''
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    # Simple HTML tag removal
                    import re
                    body += re.sub('<[^<]+?>', '', html_content)
    else:
        if payload['mimeType'] == 'text/plain':
            data = payload['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    
    return body

def get_emails(service, max_results=10, query=''):
    """Fetch emails from Gmail"""
    try:
        # List messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print('No messages found.')
            return []
        
        email_list = []
        
        # Get full message details
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = extract_email_body(message['payload'])
            
            email_data = {
                'id': msg['id'],
                'subject': subject,
                'from': sender,
                'date': date,
                'snippet': message.get('snippet', ''),
                'body': body
            }
            
            email_list.append(email_data)
        
        return email_list
        
    except HttpError as error:
        print(f'An error occurred: {error}')
        return []

def main():
    """Main function to fetch and display emails"""
    print("Connecting to Gmail...")
    
    try:
        service = get_gmail_service()
        print("Connected successfully!")
        print()
        
        # Fetch the newest emails
        emails = get_emails(service, max_results=NUM_EMAILS)
        
        if emails:
            print(f"Found {len(emails)} email(s):\n")
            for i, email_data in enumerate(emails, 1):
                print("=" * 60)
                print(f"Email {i}:")
                print("=" * 60)
                print(f"Subject: {email_data['subject']}")
                print(f"From: {email_data['from']}")
                print(f"Date: {email_data['date']}")
                print(f"\nBody:")
                print(email_data['body'] if email_data['body'] else email_data['snippet'])
                print("\n")
        else:
            print("No emails found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
