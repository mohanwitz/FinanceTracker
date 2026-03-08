"""Gmail API client: list and fetch transaction emails, mark as read."""
import base64
import email.utils
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Iterator, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    GMAIL_LABEL,
    GMAIL_QUERY,
    GOOGLE_CREDENTIALS_PATH,
    GOOGLE_TOKEN_PATH,
    LAST_RUN_FILE,
)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/spreadsheets",
]

logger = logging.getLogger(__name__)


def _get_credentials() -> Credentials | None:
    """Load or refresh OAuth credentials."""
    creds = None
    if GOOGLE_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CREDENTIALS_PATH.exists():
                logger.error("Credentials file not found: %s", GOOGLE_CREDENTIALS_PATH)
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GOOGLE_CREDENTIALS_PATH), SCOPES
            )
            creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(GOOGLE_TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return creds


def read_last_run() -> datetime | None:
    """Return last run timestamp or None if not set."""
    if not LAST_RUN_FILE.exists():
        return None
    try:
        text = LAST_RUN_FILE.read_text().strip()
        return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
    except (ValueError, OSError):
        return None


def write_last_run(ts: datetime) -> None:
    """Persist last run timestamp."""
    LAST_RUN_FILE.write_text(ts.isoformat())


def _decode_body(payload: dict[str, Any]) -> str:
    """Recursively extract plain text or HTML (as fallback) from Gmail message payload."""
    mime_type = payload.get("mimeType")
    parts = payload.get("parts", [])
    data = payload.get("body", {}).get("data")

    # 1. Handle single-part text
    if data and mime_type == "text/plain":
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # 2. Handle single-part HTML (if no plain text found yet)
    if data and mime_type == "text/html":
        raw = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

        return re.sub(r"<[^>]+>", " ", raw).strip()

    # 3. Handle multipart (recursive)
    if parts:
        # Priority 1: Look for text/plain in any part
        for part in parts:
            if part.get("mimeType") == "text/plain":
                res = _decode_body(part)
                if res:
                    return res

        # Priority 2: Look for text/html in any part
        for part in parts:
            if part.get("mimeType") == "text/html":
                res = _decode_body(part)
                if res:
                    return res

        # Priority 3: Recurse into other multiparts (like multipart/mixed or multipart/related)
        for part in parts:
            if part.get("mimeType", "").startswith("multipart/"):
                res = _decode_body(part)
                if res:
                    return res

    return ""


def _strip_html_and_headers(raw: str) -> str:
    """Reduce email to plain text for parsing."""

    text = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]


def list_and_fetch_messages(
    mark_read: bool = True,
) -> Iterator[tuple[str, str, str, datetime]]:
    """
    List messages (since last run or by label/query), fetch body, optionally mark read.
    Yields (message_id, subject, body_plain, received_date) for each message.
    """
    creds = _get_credentials()
    if not creds:
        return
    service = build("gmail", "v1", credentials=creds)

    # Build query: after last run (or default last 24h if first run), and optional label/query
    after = read_last_run()
    if not after:
        after = datetime.now(timezone.utc) - timedelta(days=1)
    
    logger.info("Fetching messages after: %s", after.isoformat())
    
    query_parts = []
    after_epoch = int(after.timestamp())
    query_parts.append(f"after:{after_epoch}")
    if GMAIL_QUERY:
        query_parts.append(GMAIL_QUERY)
    query = " ".join(query_parts) if query_parts else None

    # List messages (optionally in label)
    list_kw: dict[str, Any] = {"userId": "me", "maxResults": 100}
    if query:
        list_kw["q"] = query
    if GMAIL_LABEL:
        list_kw["labelIds"] = [GMAIL_LABEL]

    try:
        result = service.users().messages().list(**list_kw).execute()
    except Exception as e:
        logger.exception("Gmail list failed: %s", e)
        raise

    messages = result.get("messages", [])
    if not messages:
        logger.info("No new messages")
        return

    for msg_ref in messages:
        msg_id = msg_ref["id"]
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except Exception as e:
            logger.warning("Failed to get message %s: %s", msg_id, e)
            continue

        payload = msg.get("payload", {})
        headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
        subject = headers.get("subject", "")
        date_str = headers.get("date", "")
        try:
            parsed_date = email.utils.parsedate_to_datetime(date_str)
        except (TypeError, ValueError):
            parsed_date = datetime.now(timezone.utc)

        body_raw = _decode_body(payload)
        body_plain = _strip_html_and_headers(body_raw) if body_raw else ""

        yield msg_id, subject, body_plain, parsed_date

        if mark_read:
            try:
                service.users().messages().modify(
                    userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            except Exception as e:
                logger.warning("Failed to mark message %s read: %s", msg_id, e)

    return
