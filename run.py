"""Entrypoint: load config, fetch Gmail, parse with OpenAI, write to Google Sheets."""
import logging
import sys

from config import LOG_FILE, OPENAI_API_KEY, SPREADSHEET_ID
from gmail_client import list_and_fetch_messages
from parser import parse_transaction_email, ParsedTransaction
from sheets_client import append_transactions, get_existing_message_ids, update_daily_and_monthly


def setup_logging() -> None:
    """Log to file and stdout."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    if not root.handlers:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        root.addHandler(sh)


def main() -> int:
    setup_logging()
    logger = logging.getLogger(__name__)

    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set in .env")
        return 1
    if not SPREADSHEET_ID:
        logger.error("SPREADSHEET_ID not set in .env")
        return 1

    try:
        existing_ids = get_existing_message_ids()
    except Exception as e:
        logger.warning("Could not load existing message IDs: %s", e)
        existing_ids = set()

    transactions: list[ParsedTransaction] = []
    try:
        for message_id, subject, body, email_date in list_and_fetch_messages(mark_read=True):
            if message_id in existing_ids:
                logger.debug("Skip already processed: %s", message_id)
                continue
            parsed = parse_transaction_email(message_id, subject, body, email_date)
            if parsed:
                transactions.append(parsed)
                logger.info("Parsed: %s -> %s %.2f %s", message_id, parsed.merchant, parsed.amount or 0, parsed.category)
    except Exception as e:
        logger.exception("Gmail or parse failed: %s", e)
        return 1

    if not transactions:
        logger.info("No new transactions to write")
        try:
            update_daily_and_monthly()
        except Exception as e:
            logger.exception("Update daily/monthly failed: %s", e)
            return 1
        return 0

    try:
        append_transactions(transactions)
        update_daily_and_monthly()
    except Exception as e:
        logger.exception("Sheets write failed: %s", e)
        return 1

    logger.info("Done: %d transactions written", len(transactions))
    return 0


if __name__ == "__main__":
    sys.exit(main())
