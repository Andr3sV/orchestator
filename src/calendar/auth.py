"""Google OAuth2 auth: load credentials from env or token file."""

import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

from src.config import get_settings

logger = logging.getLogger(__name__)


def get_credentials() -> Credentials | None:
    """
    Return Google OAuth2 credentials from env (GOOGLE_*).
    Refreshes access token if we have refresh_token.
    """
    s = get_settings()
    if not s.google_client_id or not s.google_client_secret:
        return None
    token = s.google_refresh_token or s.google_access_token
    if not token:
        return None
    # Prefer refresh token for long-lived use
    if s.google_refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=s.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=s.google_client_id,
            client_secret=s.google_client_secret,
            scopes=[
                "https://www.googleapis.com/auth/calendar.events.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ],
        )
        try:
            creds.refresh(Request())
        except RefreshError:
            logger.warning(
                "Google Calendar: refresh token invalid or expired. "
                "Re-run: python3 scripts/setup_calendar_oauth.py"
            )
            return None
        return creds
    if s.google_access_token:
        return Credentials(
            token=s.google_access_token,
            refresh_token=None,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=s.google_client_id,
            client_secret=s.google_client_secret,
            scopes=[
                "https://www.googleapis.com/auth/calendar.events.readonly",
                "https://www.googleapis.com/auth/gmail.send",
            ],
        )
    return None
