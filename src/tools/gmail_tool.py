"""
src/tools/gmail_tool.py — Email sending tool.

Combines Gmail Toolkit (via OAuth token.json / GmailSendMessage) and 
Gmail SMTP fallback (via GMAIL_SENDER_EMAIL & GMAIL_APP_PASSWORD) 
to ensure real, reliable email delivery to the recipient's inbox.
"""
from __future__ import annotations

import base64
import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path

from langchain_core.tools import tool
from langchain_community.agent_toolkits import GmailToolkit
from langchain_community.tools.gmail.send_message import GmailSendMessage
from langchain_community.tools.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)

from src.config import _ROOT, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET


def _ensure_credentials_file() -> Path | None:
    """Ensure credentials.json exists if CLIENT_ID and CLIENT_SECRET are available in .env."""
    creds_path = _ROOT / "credentials.json"
    if creds_path.exists():
        return creds_path

    client_id = GMAIL_CLIENT_ID or os.getenv("CLIENT_ID", "")
    client_secret = GMAIL_CLIENT_SECRET or os.getenv("CLIENT_SECRET", "")

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


def _get_gmail_resource():
    """Build and return the Gmail API resource if token.json exists."""
    creds_path = _ensure_credentials_file()
    token_path = _ROOT / "token.json"

    # Only attempt OAuth if token.json already exists to avoid blocking local_server prompt
    if not token_path.exists():
        return None

    try:
        credentials = get_gmail_credentials(
            token_file=str(token_path),
            client_secrets_file=str(creds_path) if creds_path and creds_path.exists() else None,
            scopes=["https://mail.google.com/"],
        )
        return build_resource_service(credentials=credentials)
    except Exception:
        return None


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient address with a subject and body.

    Use this when asked to email an investment report, executive summary, or findings.

    Args:
        to: Recipient email address (e.g. "client@example.com").
        subject: Subject line of the email.
        body: The full text content of the email.

    Returns:
        Status message confirming whether the email was physically sent or if authentication is required.
    """
    # 1. Try Gmail SMTP if GMAIL_SENDER_EMAIL & GMAIL_APP_PASSWORD exist
    sender_email = os.getenv("GMAIL_SENDER_EMAIL", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()

    if sender_email and app_password:
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["From"] = sender_email
            msg["To"] = to
            msg["Subject"] = subject

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, app_password)
                server.send_message(msg)

            return f"✅ EMAIL DELIVERED SUCCESSFULLY to {to} via Gmail SMTP with subject: '{subject}'."
        except Exception as e:
            return f"⚠️ SMTP Dispatch error to {to}: {e}."

    # 2. Try Gmail Toolkit (OAuth API) if token.json exists
    api_resource = _get_gmail_resource()
    if api_resource is not None:
        try:
            send_tool = GmailSendMessage(api_resource=api_resource)
            to_list = [to] if isinstance(to, str) else to
            res = send_tool.invoke({
                "message": body,
                "to": to_list,
                "subject": subject,
            })
            return f"✅ EMAIL DELIVERED SUCCESSFULLY to {to} via Gmail API Toolkit! Result: {res}"
        except Exception as e:
            return f"⚠️ Gmail Toolkit Dispatch error: {e}"

    # 3. Explicit notification when email could NOT be physically sent due to missing credentials
    return (
        f"⚠️ EMAIL NOT DELIVERED (AUTHENTICATION REQUIRED)\n\n"
        f"The email could not be physically transmitted to '{to}' because Gmail credentials are not configured in your `.env` file.\n\n"
        f"--- Prepared Email Content ---\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"{'─' * 40}\n"
        f"{body}\n"
        f"{'─' * 40}\n\n"
        f"💡 TO DELIVER REAL EMAILS TO RECIPIENT INBOXES:\n"
        f"Add these 2 lines to your `.env` file in the project root:\n"
        f"GMAIL_SENDER_EMAIL=\"your.email@gmail.com\"\n"
        f"GMAIL_APP_PASSWORD=\"your-16-character-app-password\"\n\n"
        f"(Generate an App Password in 10s at: Google Account -> Security -> 2-Step Verification -> App Passwords)"
    )
