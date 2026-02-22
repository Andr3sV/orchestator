#!/usr/bin/env python3
"""
One-time script to obtain Google OAuth2 tokens for Calendar and Gmail APIs.
Run locally, complete the browser flow, then copy GOOGLE_REFRESH_TOKEN to .env.

Requires: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET in .env (from Google Cloud Console).

If you already had a token with only Calendar scope, run this script again to add
Gmail send scope; the new refresh token will include both Calendar and Gmail.
"""

import os
import sys
from pathlib import Path

DEFAULT_OAUTH_PORT = 8080

# Add project root and load .env before reading env vars
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root))

try:
    from dotenv import load_dotenv
    load_dotenv(_project_root / ".env")
except ImportError:
    pass

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]


def main():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env or environment.")
        print("Create OAuth 2.0 credentials (Desktop or Web app) in Google Cloud Console.")
        print("For Web app, add redirect URI: http://localhost:8080/")
        sys.exit(1)

    try:
        port = int(os.environ.get("OAUTH_PORT", DEFAULT_OAUTH_PORT))
    except ValueError:
        port = DEFAULT_OAUTH_PORT
    redirect_uri = f"http://localhost:{port}/"

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [redirect_uri],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    try:
        creds = flow.run_local_server(port=port, prompt="consent")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Port {port} is already in use (e.g. the bot is running).")
            print("Either stop the bot and run this script again, or use another port:")
            print("  OAUTH_PORT=8081 python3 scripts/setup_calendar_oauth.py")
            print("(Add http://localhost:8081/ to your OAuth client redirect URIs in Google Cloud Console.)")
        raise
    print("\nAdd these to your .env:\n")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    if creds.token:
        print(f"GOOGLE_ACCESS_TOKEN={creds.token}")
    print("\nThen restart the bot.")


if __name__ == "__main__":
    main()
