#!/usr/bin/env python3
"""
One-time script to obtain Google OAuth2 tokens for Calendar API.
Run locally, complete the browser flow, then copy GOOGLE_REFRESH_TOKEN to .env.

Requires: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET in .env (from Google Cloud Console).
"""

import os
import sys

# Add project root so we can import src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/calendar.events.readonly"]


def main():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env or environment.")
        print("Create OAuth 2.0 credentials (Desktop app) in Google Cloud Console.")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost:8080/"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
    )
    creds = flow.run_local_server(port=8080)
    print("\nAdd these to your .env:\n")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    if creds.token:
        print(f"GOOGLE_ACCESS_TOKEN={creds.token}")
    print("\nThen restart the bot.")


if __name__ == "__main__":
    main()
