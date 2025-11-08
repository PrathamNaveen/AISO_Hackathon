from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file("token.json")
service = build("gmail", "v1", credentials=creds)

def get_event_emails():
    results = service.users().messages().list(
        userId='me', q="subject:Invitation OR subject:Event", maxResults=5
    ).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        email = service.users().messages().get(userId='me', id=msg['id']).execute()
        emails.append(email['snippet'])
    return emails

# Test
for email in get_event_emails():
    print("📧 Email snippet:", email)
