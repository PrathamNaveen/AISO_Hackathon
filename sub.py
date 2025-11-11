from dotenv import load_dotenv
import os
import json
import time
import base64
from google.cloud import pubsub_v1
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from db import insert_email

load_dotenv()

# --- Pub/Sub Setup ---
project_id = "aiso-477615"
subscription_id = "GmailTopic-sub"

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)

# --- Gmail API ---
def get_gmail_service():
    """Create a fresh Gmail service instance"""
    creds = Credentials.from_authorized_user_file("token.json")
    return build("gmail", "v1", credentials=creds)

# --- Process a single message ---
def process_new_message(service, msg_id):
    try:
        email = service.users().messages().get(
            userId="me",
            id=msg_id,
            format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in email.get("payload", {}).get("headers", [])}
        sender = headers.get("From", "Unknown")
        subject = headers.get("Subject", "No Subject")
        date = headers.get("Date")

        # Extract plain text body
        body = ""
        parts = email.get("payload", {}).get("parts", [])
        for part in parts:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data")
                if data:
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    break

        print(f"📬 New Email from {sender}: {subject}")

        user_email = "prathamnaveen.m@gmail.com"

        insert_email(sender, subject, body, user_email)
        print("✅ Stored in PostgreSQL")

    except Exception as e:
        print(f"❌ Error fetching message {msg_id}: {e}")

# --- Pub/Sub Callback ---
def callback(message):
    try:
        data = json.loads(message.data.decode("utf-8"))
        print(f"\n📧 Notification received at {time.strftime('%H:%M:%S')}")

        service = get_gmail_service()

        # Fetch recent messages from INBOX (latest first)
        result = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=5).execute()
        messages = result.get("messages", [])

        if messages:
            for msg in messages:
                process_new_message(service, msg["id"])

        message.ack()
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        if "ssl" in str(e).lower():
            message.ack()
        else:
            message.nack()

# --- Start Listening ---
print(f"🎧 Listening on: {subscription_path}")
print(f"⏰ Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    streaming_pull_future.result()
except KeyboardInterrupt:
    print("\n👋 Shutting down...")
    streaming_pull_future.cancel()
