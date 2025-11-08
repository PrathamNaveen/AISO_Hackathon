# Fix OAuth Redirect URI Error

## Quick Fix Steps

If you're seeing this error:
> "You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policy"

Follow these steps:

### 1. Go to Google Cloud Console
- Visit: https://console.cloud.google.com/
- Select your project

### 2. Navigate to Credentials
- Go to **"APIs & Services"** > **"Credentials"**
- Find your **OAuth 2.0 Client ID** (Desktop application)
- Click on it to edit

### 3. Add Redirect URI
- Scroll down to **"Authorized redirect URIs"**
- Click **"+ ADD URI"**
- Add: `http://localhost:8080`
- Click **"SAVE"**

### 4. Update Your credentials.json (if needed)
If you already downloaded your credentials.json, make sure it includes the redirect URI:
```json
{
  "installed": {
    "client_id": "...",
    "client_secret": "...",
    "redirect_uris": ["http://localhost:8080"]
  }
}
```

### 5. Run the Script Again
```bash
python main.py
```

## Alternative: Use Different Port

If port 8080 is already in use, you can change it:

1. Edit `main.py` and change:
   ```python
   REDIRECT_PORT = 8080  # Change to your preferred port
   ```

2. Register that port in Google Cloud Console:
   - Add `http://localhost:YOUR_PORT` to Authorized redirect URIs

## Notes

- The redirect URI must **exactly match** what's registered in Google Cloud Console
- For Desktop applications, `http://localhost:PORT` is the standard format
- Changes in Google Cloud Console may take a few minutes to propagate

