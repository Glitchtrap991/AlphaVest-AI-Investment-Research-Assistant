"""
src/tools/gmail_tool.py — Email sending tool using latest langchain_google_community GmailToolkit.

Uses the official langchain_google_community integration package to format credentials
and send emails via Gmail API.
"""
from __future__ import annotations

import inspect
import json
import os
from pathlib import Path

from langchain_core.tools import tool

try:
    from langchain_google_community import GmailToolkit
    from langchain_google_community.gmail.send_message import GmailSendMessage
    from langchain_google_community.gmail.utils import (
        build_resource_service,
        get_gmail_credentials,
    )
except ImportError:
    from langchain_community.agent_toolkits import GmailToolkit
    from langchain_community.tools.gmail.send_message import GmailSendMessage
    from langchain_community.tools.gmail.utils import (
        build_resource_service,
        get_gmail_credentials,
    )

from src.config import _ROOT, GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET


def _ensure_credentials_file() -> Path | None:
    """Ensure credentials.json exists in standard Google OAuth 2.0 format."""
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
    """Build and return the Gmail API resource using credentials/token."""
    creds_path = _ensure_credentials_file()
    token_path = _ROOT / "token.json"

    if not (token_path.exists() or (creds_path and creds_path.exists())):
        return None

    try:
        kwargs = {
            "token_file": str(token_path) if token_path.exists() else None,
            "scopes": ["https://mail.google.com/"],
        }
        if creds_path and creds_path.exists():
            sig = inspect.signature(get_gmail_credentials)
            if "client_sercret_file" in sig.parameters:
                kwargs["client_sercret_file"] = str(creds_path)
            elif "client_secrets_file" in sig.parameters:
                kwargs["client_secrets_file"] = str(creds_path)

        credentials = get_gmail_credentials(**kwargs)
        return build_resource_service(credentials=credentials)
    except Exception:
        return None


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail Toolkit.

    Use this when asked to email an investment report, summary, or analysis.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: The full email body text.

    Returns:
        Confirmation message of email dispatch status.
    """
    api_resource = _get_gmail_resource()

    if api_resource is not None:
        try:
            toolkit = GmailToolkit(api_resource=api_resource)
            send_tool = GmailSendMessage(api_resource=api_resource)

            to_list = [to] if isinstance(to, str) else to
            res = send_tool.invoke({
                "message": body,
                "to": to_list,
                "subject": subject,
            })
            return f"✅ Email sent via Gmail Toolkit to {to} with subject '{subject}'. Result: {res}"
        except Exception as e:
            return (
                f"⚠️ Gmail Toolkit send error: {e}\n\n"
                f"Email Preview:\nTo: {to}\nSubject: {subject}\n\n{body}"
            )

    # Fallback preview mode when credentials/token file not yet authenticated
    return (
        f"📧 [Gmail Toolkit — Preview]\n\n"
        f"To: {to}\n"
        f"Subject: {subject}\n"
        f"{'─' * 40}\n"
        f"{body}\n"
        f"{'─' * 40}\n\n"
        f"Note: To dispatch emails using Gmail Toolkit, place your `credentials.json` or `token.json` "
        f"in the project root directory."
    )
