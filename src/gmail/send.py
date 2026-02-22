"""Send email via Gmail API using shared Google OAuth credentials."""

import base64
import logging
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.calendar.auth import get_credentials

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """
    Send a plain-text email via Gmail API.
    Uses the same OAuth credentials as Calendar (must include gmail.send scope).
    Raises on missing credentials or API errors.
    """
    creds = get_credentials()
    if not creds:
        raise ValueError(
            "Google credentials not configured or invalid. "
            "Set GOOGLE_* in .env and run: python3 scripts/setup_calendar_oauth.py"
        )
    message = MIMEText(body, "plain", "utf-8")
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service = build("gmail", "v1", credentials=creds)
    try:
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
    except HttpError as e:
        logger.exception("Gmail API error sending email")
        raise RuntimeError(
            "No pude enviar el email; revisa permisos o intenta más tarde."
        ) from e
