"""Load .env and application config."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
LAST_RUN_FILE = PROJECT_ROOT / "last_run.txt"
LOG_FILE = PROJECT_ROOT / "finance_tracker.log"

# Secrets and IDs
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "").strip()

# Gmail
GMAIL_LABEL = os.getenv("GMAIL_LABEL", "").strip()
GMAIL_QUERY = os.getenv("GMAIL_QUERY", '"amount" ("debit" OR "transaction" OR "purchased" OR "alert")').strip()
GOOGLE_CREDENTIALS_PATH = Path(
    os.getenv("GOOGLE_CREDENTIALS_PATH", PROJECT_ROOT / "credentials.json")
)
GOOGLE_TOKEN_PATH = Path(
    os.getenv("GOOGLE_TOKEN_PATH", PROJECT_ROOT / "token.json")
)

# Fixed categories for consistent daily/monthly breakdowns
CATEGORIES = [
    "Food & Dining",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Other",
]

# Sheet names
SHEET_TRANSACTIONS = "Transactions"
SHEET_DAILY = "Daily"
SHEET_MONTHLY = "Monthly"
