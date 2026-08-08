"""
src/tools/gmail_tool.py — Email sending tool.

Uses the Gmail toolkit when credentials are available.
Falls back to a stub that returns the email content if not configured.
"""
from __future__ import annotations
import os
from pathlib import Path

from langchain_core.tools import tool

from src.config import _ROOT


def _gmail_available() -> bool:
    """Check if Gmail OAuth credentials exist."""
    creds_path = _ROOT / "credentials.json"
    token_path = _ROOT / "token.json"
    return creds_path.exists() or token_path.exists()


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail to a client or colleague.

    Use this when the user asks you to email a report, summary, or any
    content to someone.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: The full email body text.

    Returns:
        Confirmation message or the email content if Gmail is not configured.
    """
    if _gmail_available():
        try:
            from langchain_google_community.gmail.utils import (
                build_resource_service,
                get_gmail_credentials,
            )

            credentials = get_gmail_credentials(
                token_file=str(_ROOT / "token.json"),
                client_sercret_file=str(_ROOT / "credentials.json"),
                scopes=["https://mail.google.com/"],
            )
            api_resource = build_resource_service(credentials=credentials)

            import base64
            from email.mime.text import MIMEText

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            api_resource.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            return f"✅ Email sent to {to} with subject '{subject}'."
        except Exception as e:
            return f"⚠️ Gmail send failed: {e}. Email content below:\n\nTo: {to}\nSubject: {subject}\n\n{body}"
    else:
        # Stub mode: show what would be sent
        return (
            f"📧 [Gmail not configured — showing email preview]\n\n"
            f"To: {to}\n"
            f"Subject: {subject}\n"
            f"{'─' * 40}\n"
            f"{body}\n"
            f"{'─' * 40}\n\n"
            f"To enable real email sending, place a `credentials.json` file "
            f"from Google Cloud Console (with Gmail API enabled) in the project root."
        )
