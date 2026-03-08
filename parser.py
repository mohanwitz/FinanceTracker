"""Parse transaction email content with OpenAI: extract fields and categorize."""
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from openai import OpenAI

from config import CATEGORIES, OPENAI_API_KEY

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are a financial transaction parser. Given the subject and body of a transaction/alert email (e.g. from a bank or card), extract structured data.

Respond with a single JSON object only, no other text. Use exactly these keys:
- "transaction_date": date of the transaction in YYYY-MM-DD format (use the date from the email; if missing, use today)
- "amount": numeric amount spent (positive number; if it's a credit/refund use a negative number)
- "merchant": short name of the vendor/merchant/description
- "category": exactly one of: {json.dumps(CATEGORIES)}

If the email does not describe a single clear transaction (e.g. statement summary, login alert, promotional email, newsletter, system update, balance update), set "amount" to null, "merchant" to a short summary, and "category" to "Other".

Output only valid JSON. If it's absolutely not a transaction, you can return {"amount": null, "merchant": "Non-transactional", "category": "Other"}.
"""


@dataclass
class ParsedTransaction:
    """Structured transaction from email + OpenAI."""
    transaction_date: str  # YYYY-MM-DD
    amount: float | None
    merchant: str
    category: str
    raw_subject: str
    message_id: str
    email_date: str  # YYYY-MM-DD
    needs_review: bool = False


def parse_transaction_email(
    message_id: str,
    subject: str,
    body: str,
    email_date: datetime,
    api_key: str | None = None,
) -> ParsedTransaction | None:
    """
    Call OpenAI to extract transaction_date, amount, merchant, category from email.
    Returns ParsedTransaction or None if parsing fails. Uses "Uncategorized" and needs_review on failure.
    """
    key = (api_key or OPENAI_API_KEY).strip()
    if not key:
        logger.error("OPENAI_API_KEY not set")
        return None

    combined = f"Subject: {subject}\n\n{body}".strip()
    if not combined or len(combined) < 10:
        logger.warning("Email content too short to parse")
        return None

    client = OpenAI(api_key=key)
    email_date_str = email_date.strftime("%Y-%m-%d")

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": combined[:12000]},
            ],
            temperature=0,
        )
        text = (response.choices[0].message.content or "").strip()
        logger.info("OpenAI raw response for %s: %s", message_id, text)
        # Strip markdown code block if present
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        data: dict[str, Any] = json.loads(text)
        logger.info("OpenAI parsed: transaction_date=%s amount=%s merchant=%s category=%s", data.get("transaction_date"), data.get("amount"), data.get("merchant"), data.get("category"))
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.warning("OpenAI response parse error: %s", e)
        return _fallback_transaction(message_id, subject, email_date_str, needs_review=True)
    except Exception as e:
        logger.exception("OpenAI API error: %s", e)
        return None

    trans_date = data.get("transaction_date") or email_date_str
    amount_raw = data.get("amount")
    amount: float | None = None
    if amount_raw is not None:
        try:
            amount = float(amount_raw)
        except (TypeError, ValueError):
            pass
    merchant = (data.get("merchant") or "Unknown").strip() or "Unknown"
    category = (data.get("category") or "Other").strip()
    if category not in CATEGORIES:
        category = "Other"

    needs_review = amount is None and (amount_raw is not None or "transaction" in combined.lower())
    return ParsedTransaction(
        transaction_date=trans_date,
        amount=amount,
        merchant=merchant,
        category=category,
        raw_subject=subject,
        message_id=message_id,
        email_date=email_date_str,
        needs_review=needs_review,
    )


def _fallback_transaction(
    message_id: str,
    subject: str,
    email_date_str: str,
    needs_review: bool = True,
) -> ParsedTransaction:
    """Build a minimal transaction for storage when parsing fails."""
    return ParsedTransaction(
        transaction_date=email_date_str,
        amount=None,
        merchant=subject[:100] or "Unknown",
        category="Other",
        raw_subject=subject,
        message_id=message_id,
        email_date=email_date_str,
        needs_review=needs_review,
    )
