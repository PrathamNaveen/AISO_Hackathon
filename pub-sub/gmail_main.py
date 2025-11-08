from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Load OAuth credentials
creds = Credentials.from_authorized_user_file("token.json")
service = build("gmail", "v1", credentials=creds)

# Start watching the mailbox
watch_request = {
    "labelIds": ["INBOX"],           # Only watch inbox
    "topicName": "projects/aiso-477615/topics/gmail-updates"
}

response = service.users().watch(userId="me", body=watch_request).execute()
print("✅ Gmail watch started:", response)
