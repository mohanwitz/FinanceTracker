"""Entrypoint: load config, fetch Gmail, parse with OpenAI, write to Google Sheets."""
import logging
import sys
from datetime import datetime

from config import LOG_FILE, OPENAI_API_KEY, SPREADSHEET_ID
from gmail_client import list_and_fetch_messages, write_last_run
from parser import ParsedTransaction, parse_transaction_email
from sheets_client import append_transactions, get_existing_message_ids, update_daily_and_monthly


logger = logging.getLogger(__name__)


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

    try:
        if transactions:
            append_transactions(transactions)
            logger.info("Done: %d transactions written", len(transactions))
        else:
            logger.info("No new transactions to write")

        update_daily_and_monthly()
    except Exception as e:
        logger.exception("Sheets update or append failed: %s", e)
        return 1

    write_last_run(datetime.utcnow())
    return 0


if __name__ == "__main__":
    sys.exit(main())
