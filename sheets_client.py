"""Google Sheets client: append transactions, update daily and monthly summaries."""
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from googleapiclient.discovery import build

from config import (
    CATEGORIES,
    SHEET_DAILY,
    SHEET_MONTHLY,
    SHEET_TRANSACTIONS,
    SPREADSHEET_ID,
)
from gmail_client import _get_credentials
from parser import ParsedTransaction

logger = logging.getLogger(__name__)

TRANSACTION_HEADERS = [
    "email_date",
    "transaction_date",
    "amount",
    "merchant",
    "category",
    "raw_subject",
    "message_id",
    "needs_review",
]


def _sheets_service():
    """Build Sheets API service using same OAuth as Gmail (shared token with spreadsheets scope)."""
    creds = _get_credentials()
    return build("sheets", "v4", credentials=creds)


def _ensure_headers(sheet_name: str, headers: list[str]) -> None:
    """Ensure first row of sheet is headers; create sheet if missing."""
    service = _sheets_service()
    spreadsheet_id = SPREADSHEET_ID
    if not spreadsheet_id:
        raise ValueError("SPREADSHEET_ID not set in .env")

    try:
        meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta.get("sheets", [])}
    except Exception as e:
        logger.exception("Sheets get failed: %s", e)
        raise

    if sheet_name not in sheet_ids:
        body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {"title": sheet_name},
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        sheet_ids = {s["properties"]["title"]: s["properties"]["sheetId"] for s in service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute().get("sheets", [])}

    range_name = f"'{sheet_name}'!A1:Z1"
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": [headers]},
    ).execute()


def _col_letter(n: int) -> str:
    """Column letter(s) for 1-based index n: 1=A, 9=I, 27=AA."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s or "A"


def _clear_sheet_data(service: Any, spreadsheet_id: str, sheet_name: str, start_row: int = 2, max_rows: int = 500) -> None:
    """Clear data rows (leave header) so old/stale rows don't remain."""
    end_row = start_row + max_rows - 1
    range_to_clear = f"'{sheet_name}'!A{start_row}:I{end_row}"
    try:
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_to_clear,
        ).execute()
    except Exception as e:
        logger.debug("Clear sheet %s (optional): %s", sheet_name, e)


def get_existing_message_ids() -> set[str]:
    """Read message_id column from Transactions sheet to skip duplicates."""
    if not SPREADSHEET_ID:
        return set()
    service = _sheets_service()
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{SHEET_TRANSACTIONS}'!G:G",
            )
            .execute()
        )
    except Exception as e:
        logger.warning("Could not read existing message IDs: %s", e)
        return set()
    rows = result.get("values", [])
    # First row is header "message_id"
    ids = set()
    for row in rows[1:]:
        if row and row[0]:
            ids.add(str(row[0]).strip())
    return ids


def append_transactions(transactions: list[ParsedTransaction]) -> None:
    """Append new transaction rows to Transactions sheet; skip duplicates by message_id. Only appends rows with a non-zero amount."""
    if not SPREADSHEET_ID:
        raise ValueError("SPREADSHEET_ID not set in .env")
    existing = get_existing_message_ids()
    # Only include transactions that have a value (non-null, non-zero amount)
    with_value = [t for t in transactions if t.message_id not in existing and t.amount is not None and t.amount != 0]
    to_append = with_value
    if not to_append:
        logger.info("No new transactions with value to append (already in sheet or amount is zero)")
        return

    service = _sheets_service()
    range_name = f"'{SHEET_TRANSACTIONS}'!A:H"
    # Ensure headers exist on first run
    try:
        service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_TRANSACTIONS}'!A1:H1",
        ).execute()
    except Exception:
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{SHEET_TRANSACTIONS}'!A1:H1",
            valueInputOption="USER_ENTERED",
            body={"values": [TRANSACTION_HEADERS]},
        ).execute()

    rows = []
    for t in to_append:
        rows.append([
            t.email_date,
            t.transaction_date,
            t.amount if t.amount is not None else "",
            t.merchant,
            t.category,
            t.raw_subject[:500] if t.raw_subject else "",
            t.message_id,
            "yes" if t.needs_review else "no",
        ])
    body = {"values": rows}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    logger.info("Appended %d transactions to sheet", len(rows))


# Column indices when reading Transactions sheet (A=0, B=1, ...); order must match TRANSACTION_HEADERS
_TRANSACTION_COL_EMAIL_DATE = 0
_TRANSACTION_COL_TRANS_DATE = 1
_TRANSACTION_COL_AMOUNT = 2
_TRANSACTION_COL_MERCHANT = 3
_TRANSACTION_COL_CATEGORY = 4


def _read_all_transactions() -> list[dict[str, Any]]:
    """Read all rows from Transactions sheet (after header). Uses fixed column indices so we don't depend on header text."""
    if not SPREADSHEET_ID:
        return []
    service = _sheets_service()
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"'{SHEET_TRANSACTIONS}'!A:H",
            )
            .execute()
        )
    except Exception as e:
        logger.warning("Could not read transactions: %s", e)
        return []
    values = result.get("values", [])
    if not values:
        return []
    logger.info("Transactions sheet: header row=%s; first data row (raw)=%s", values[0] if values else [], values[1] if len(values) > 1 else [])
    # Skip first row (header); use fixed column positions: A=email_date, B=transaction_date, C=amount, D=merchant, E=category
    rows = []
    for row in values[1:]:
        if len(row) < 3:
            continue
        email_date_val = row[_TRANSACTION_COL_EMAIL_DATE] if len(row) > _TRANSACTION_COL_EMAIL_DATE else ""
        trans_date_val = row[_TRANSACTION_COL_TRANS_DATE] if len(row) > _TRANSACTION_COL_TRANS_DATE else ""
        amount_val = row[_TRANSACTION_COL_AMOUNT] if len(row) > _TRANSACTION_COL_AMOUNT else ""
        merchant_val = row[_TRANSACTION_COL_MERCHANT] if len(row) > _TRANSACTION_COL_MERCHANT else ""
        category_val = row[_TRANSACTION_COL_CATEGORY] if len(row) > _TRANSACTION_COL_CATEGORY else ""

        # Normalize date: Sheets may return serial number or string
        def _date_str(v: Any) -> str:
            if v is None or v == "":
                return ""
            if isinstance(v, (int, float)):
                try:
                    # Excel/Sheets serial: 1 = 1899-12-30
                    epoch = datetime(1899, 12, 30)
                    d = epoch + timedelta(days=int(v))
                    return d.strftime("%Y-%m-%d")
                except Exception:
                    return ""
            s = str(v).strip()
            if len(s) >= 10 and s[:4].isdigit() and s[4:5] in "-/" and s[5:7].isdigit():
                return s[:10].replace("/", "-")
            return s[:10] if s else ""

        trans_date = _date_str(trans_date_val) or _date_str(email_date_val)
        email_date = _date_str(email_date_val) or trans_date

        try:
            amount = float(str(amount_val).replace(",", "").strip()) if amount_val not in (None, "") else 0.0
        except (ValueError, TypeError):
            amount = 0.0

        category = (str(category_val).strip() or "Other") if category_val not in (None, "") else "Other"
        if category not in CATEGORIES:
            category = "Other"

        rows.append({
            "email_date": email_date,
            "transaction_date": trans_date,
            "amount": amount,
            "merchant": str(merchant_val or "").strip(),
            "category": category,
        })
    if rows:
        total_amount = sum(r["amount"] for r in rows)
        sample = rows[:3]
        logger.info(
            "Read %d transactions from sheet (total amount=%.2f); sample: %s",
            len(rows),
            total_amount,
            [(r["transaction_date"], r["amount"], r["category"]) for r in sample],
        )
    return rows


def update_daily_and_monthly() -> None:
    """Recompute Daily and Monthly sheets from Transactions sheet data."""
    rows = _read_all_transactions()
    if not rows:
        logger.info("No transaction data to aggregate")
        return

    # Daily: date -> { total, category -> sum }; only include rows with non-zero amount
    daily: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for r in rows:
        amount = r.get("amount") or 0
        if isinstance(amount, str):
            try:
                amount = float(amount.replace(",", ""))
            except ValueError:
                amount = 0
        if amount == 0:
            continue
        trans_date = (r.get("transaction_date") or r.get("email_date") or "").strip()
        if not trans_date:
            continue
        if len(trans_date) > 10:
            trans_date = trans_date[:10]
        category = (r.get("category") or "Other").strip()
        if category not in CATEGORIES:
            category = "Other"
        daily[trans_date]["total"] += amount
        daily[trans_date][category] += amount

    # Monthly: YYYY-MM -> { total, category -> sum }
    monthly: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for date_key, agg in daily.items():
        month_key = date_key[:7] if len(date_key) >= 7 else date_key
        monthly[month_key]["total"] += agg["total"]
        for cat in CATEGORIES:
            monthly[month_key][cat] = monthly[month_key].get(cat, 0) + agg.get(cat, 0)

    service = _sheets_service()
    spreadsheet_id = SPREADSHEET_ID

    # Daily sheet: clear old data then write header + all daily rows
    daily_headers = ["Date", "Total"] + CATEGORIES
    daily_rows = [daily_headers]
    for date in sorted(daily.keys()):
        agg = daily[date]
        row = [date, agg["total"]] + [agg.get(c, 0) for c in CATEGORIES]
        daily_rows.append(row)
    _ensure_headers(SHEET_DAILY, daily_headers)
    _clear_sheet_data(service, spreadsheet_id, SHEET_DAILY, start_row=2, max_rows=500)
    if len(daily_rows) > 1:
        range_daily = f"'{SHEET_DAILY}'!A1:{_col_letter(len(daily_headers))}{len(daily_rows)}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_daily,
            valueInputOption="USER_ENTERED",
            body={"values": daily_rows},
        ).execute()
        logger.info("Updated Daily sheet with %d rows", len(daily_rows) - 1)

    # Monthly sheet: clear old data then write header + all monthly rows
    monthly_headers = ["Month", "Total"] + CATEGORIES
    monthly_rows = [monthly_headers]
    for month in sorted(monthly.keys()):
        agg = monthly[month]
        row = [month, agg["total"]] + [agg.get(c, 0) for c in CATEGORIES]
        monthly_rows.append(row)
    _ensure_headers(SHEET_MONTHLY, monthly_headers)
    _clear_sheet_data(service, spreadsheet_id, SHEET_MONTHLY, start_row=2, max_rows=100)
    if len(monthly_rows) > 1:
        range_monthly = f"'{SHEET_MONTHLY}'!A1:{_col_letter(len(monthly_headers))}{len(monthly_rows)}"
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_monthly,
            valueInputOption="USER_ENTERED",
            body={"values": monthly_rows},
        ).execute()
        logger.info("Updated Monthly sheet with %d rows", len(monthly_rows) - 1)
