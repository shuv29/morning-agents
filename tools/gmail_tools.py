import os
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (CREDENTIALS_FILE, EMAIL_LOOKBACK_HOURS, GOOGLE_SCOPES,
                    MAX_EMAILS_TO_ANALYZE, TOKEN_FILE)


def get_google_credentials() -> Credentials:
    """First run: opens browser to ask permission, saves token.json.
    Every later run: silent."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, GOOGLE_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, GOOGLE_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


import base64


def _extract_body(payload) -> str:
    """Gmail nests the body inside MIME parts. Walk them and pull plain text."""
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode(errors="ignore")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode(errors="ignore")
    for part in payload.get("parts", []):  # fallback: recurse into nested parts
        text = _extract_body(part)
        if text:
            return text
    return ""


def fetch_recent_emails() -> list[dict]:
    service = build("gmail", "v1", credentials=get_google_credentials())
    after = datetime.now() - timedelta(hours=EMAIL_LOOKBACK_HOURS)
    query = f"in:inbox after:{int(after.timestamp())}"

    result = service.users().messages().list(
        userId="me", q=query, maxResults=MAX_EMAILS_TO_ANALYZE
    ).execute()

    emails = []
    for msg_ref in result.get("messages", []):
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full"
        ).execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        body = _extract_body(msg["payload"])[:1500]  # cap per-email tokens
        emails.append({
            "sender": headers.get("From", "unknown"),
            "subject": headers.get("Subject", "(no subject)"),
            "snippet": msg.get("snippet", ""),
            "body": body,
            "date": headers.get("Date", ""),
        })
    return emails