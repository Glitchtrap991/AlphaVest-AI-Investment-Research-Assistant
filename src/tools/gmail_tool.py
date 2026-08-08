"""
src/tools/gmail_tool.py — Email sending tool.

Supports:
  1. Gmail OAuth API (via credentials.json / token.json or CLIENT_ID & CLIENT_SECRET from .env)
  2. Gmail SMTP (via GMAIL_SENDER_EMAIL & GMAIL_APP_PASSWORD in .env)
  3. Informative preview fallback if no credentials are configured.
"""
from __future__ import annotations

import base64
import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from langchain_core.tools import tool

from src.config import _ROOT, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET


def _ensure_credentials_file() -> Path | None:
    """Ensure credentials.json exists if CLIENT_ID and CLIENT_SECRET are available."""
    creds_path = _ROOT / "credentials.json"
    if creds_path.exists():
        return creds_path

    client_id = GMAIL_CLIENT_ID or os.getenv("CLIENT_ID")
    client_secret = GMAIL_CLIENT_SECRET or os.getenv("CLIENT_SECRET")

    if client_id and client_secret:
        creds_data = {
            "installed": {
                "client_id": client_id,
                "project_id": "alphavest-assistant",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["http://localhost"]
            }
        }
        creds_path.write_text(json.dumps(creds_data, indent=2), encoding="utf-8")
        return creds_path

    return None


def _gmail_oauth_available() -> bool:
    """Check if Gmail OAuth credentials file or token exists."""
    token_path = _ROOT / "token.json"
    creds_path = _ensure_credentials_file()
    return token_path.exists() or (creds_path is not None and creds_path.exists())


def _smtp_available() -> bool:
    """Check if Gmail SMTP credentials are set in environment."""
    sender = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    app_pwd = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    return bool(sender and app_pwd)


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a client or colleague.

    Use this when asked to email an investment report, summary, or analysis.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: The full email body text.

    Returns:
        Confirmation message of email dispatch status.
    """
    # 1. Try SMTP sending if App Password credentials exist
    if _smtp_available():
        sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
        app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["From"] = sender_email
            msg["To"] = to
            msg["Subject"] = subject

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.send_message(msg)

            return f"✅ Email successfully sent to {to} with subject: '{subject}'."
        except Exception as e:
            return f"⚠️ SMTP send failed to {to}: {e}. (Verify GMAIL_SENDER_EMAIL & GMAIL_APP_PASSWORD in .env)"

    # 2. Try Gmail OAuth API if OAuth credentials/token exist
    if _gmail_oauth_available():
        try:
            from langchain_google_community.gmail.utils import (
                build_resource_service,
                get_gmail_credentials,
            )

            token_file = _ROOT / "token.json"
            creds_file = _ROOT / "credentials.json"

            credentials = get_gmail_credentials(
                token_file=str(token_file) if token_file.exists() else None,
                client_sercret_file=str(creds_file) if creds_file.exists() else None,
                scopes=["https://mail.google.com/"],
            )
            api_resource = build_resource_service(credentials=credentials)

            message = MIMEText(body)
            message["to"] = to
            message["subject"] = subject

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            api_resource.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()

            return f"✅ Email sent via Gmail API to {to} with subject '{subject}'."
        except Exception as e:
            return f"⚠️ Gmail OAuth send attempt failed: {e}.\n\nTo use standard SMTP without browser login, add `GMAIL_SENDER_EMAIL` and `GMAIL_APP_PASSWORD` to your `.env` file."

    # 3. Fallback preview mode
    return (
        f"📧 [Email Preview — Credentials needed for real dispatch]\n\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"{'─' * 40}\n"
        f"{body}\n"
        f"{'─' * 40}\n\n"
        f"💡 To enable automatic email sending, add these to your `.env` file:\n"
        f"GMAIL_SENDER_EMAIL=\"your.email@gmail.com\"\n"
        f"GMAIL_APP_PASSWORD=\"your-16-char-app-password\""
    )

