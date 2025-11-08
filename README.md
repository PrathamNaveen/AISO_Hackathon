# Gmail Pub/Sub Email Polling Service

A simple Python service that polls Gmail emails and publishes them to Google Cloud Pub/Sub.

## Features

- 🔐 Gmail API integration with OAuth2 authentication
- 📧 Email polling with customizable search queries
- 📨 Google Cloud Pub/Sub integration for publishing emails
- 🔄 Continuous polling mode for real-time monitoring

## Prerequisites

1. **Google Cloud Project** with the following APIs enabled:
   - Gmail API
   - Cloud Pub/Sub API

2. **OAuth 2.0 Credentials** for Gmail API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "APIs & Services" > "Credentials"
   - Create OAuth 2.0 Client ID (Desktop application)
   - Download credentials as `credentials.json`

3. **Google Cloud Authentication**:
   - Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
   - Run `gcloud auth application-default login`

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up credentials**:
   - Place your `credentials.json` file in the project root directory
   - This file will be created when you download OAuth 2.0 credentials from Google Cloud Console

5. **Configure environment variables**:
   Create a `.env` file in the project root:
   ```bash
   # Google Cloud Configuration
   GOOGLE_CLOUD_PROJECT_ID=your-project-id
   PUBSUB_TOPIC_NAME=gmail-notifications

   ```

   Or set these as environment variables directly.

## Usage

### Basic Usage

**Single poll of unread emails**:
```bash
python main.py
```

**Process all unread emails**:
```bash
python main.py --all-unread
```

**Process emails from the last 7 days**:
```bash
python main.py --recent-days 7
```

### Continuous Polling

**Poll every 60 seconds** (default):
```bash
python main.py --mode continuous
```

**Poll with custom interval**:
```bash
python main.py --mode continuous --interval 30
```

### Advanced Options

**Custom Gmail search query**:
```bash
python main.py --query "from:example@gmail.com is:unread"
```

**Limit number of messages per poll**:
```bash
python main.py --max-results 20
```

**Combine options**:
```bash
python main.py --mode continuous --interval 120 --query "is:unread newer_than:1d" --max-results 50
```

## Configuration

### Pub/Sub Topic

The service will automatically create the Pub/Sub topic if it doesn't exist. Configure the topic name in your `.env`:
```
PUBSUB_TOPIC_NAME=gmail-notifications
```

## Gmail Search Query Examples

- `is:unread` - Unread emails
- `from:example@gmail.com` - Emails from specific sender
- `subject:urgent` - Emails with "urgent" in subject
- `newer_than:7d` - Emails from last 7 days
- `has:attachment` - Emails with attachments
- `is:unread from:boss@company.com` - Combine multiple criteria

## Pub/Sub Message Format

Messages published to Pub/Sub contain:
```json
{
  "id": "message_id",
  "threadId": "thread_id",
  "subject": "Email Subject",
  "from": "sender@example.com",
  "date": "Mon, 1 Jan 2024 12:00:00 +0000",
  "snippet": "Email preview...",
  "body": "Full email body text...",
  "labels": ["UNREAD", "INBOX"]
}
```

## Architecture

- **`gmail_client.py`**: Handles Gmail API authentication and email retrieval
- **`pubsub_client.py`**: Manages Google Cloud Pub/Sub publishing
- **`email_poller.py`**: Main service that orchestrates polling and publishing
- **`main.py`**: CLI entry point
- **`config.py`**: Configuration management

## First Run

On first run, the application will:
1. Open a browser window for OAuth authentication
2. Ask you to sign in to your Google account
3. Request permissions to read Gmail
4. Save authentication token to `token.json` for future runs

## Troubleshooting

**"credentials.json not found"**:
- Download OAuth 2.0 credentials from Google Cloud Console
- Save as `credentials.json` in the project root

**"Topic not found"**:
- Ensure Pub/Sub API is enabled in your Google Cloud project
- Check that `GOOGLE_CLOUD_PROJECT_ID` is correct
- The service will attempt to create the topic automatically

**"Permission denied"**:
- Ensure Gmail API is enabled in your Google Cloud project
- Verify OAuth scopes include `gmail.readonly`
- Re-authenticate by deleting `token.json` and running again

**Import errors**:
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

## Security Notes

- Never commit `credentials.json` or `token.json` to version control
- These files are already in `.gitignore`
- Keep your OAuth credentials secure
- Use environment variables for sensitive configuration

## License

See LICENSE file for details.
