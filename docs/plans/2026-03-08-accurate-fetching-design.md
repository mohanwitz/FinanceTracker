# FinanceTracker Accurate Fetching & Incremental Tracking Design

**Date:** 2026-03-08
**Status:** Approved

## 1. Goal
Improve the accuracy of transaction email identification and ensure the application fetches data incrementally without missing or duplicating records.

## 2. Approach
*   **Gmail Search Optimization:** Update `GMAIL_QUERY` to target keywords common in transaction alerts while excluding marketing noise.
*   **Stateful Fetching:** Persist the last-run timestamp *after* successful processing and write operations to Google Sheets.
*   **Idempotent processing:** Use both `after:{timestamp}` in Gmail and `message_id` checks in Sheets to avoid duplicates.

## 3. Architecture & Components

### 3.1 Gmail Query (Accuracy)
Updated `GMAIL_QUERY` in `config.py`:
`"amount" ("debit" OR "transaction" OR "purchased" OR "alert")`
*   This focuses on the most common markers of a financial transaction.
*   Optionally include `-subject:"newsletter" -subject:"statement"` if noise persists.

### 3.2 State Management (Incremental Fetching)
*   **File:** `last_run.txt` (stored in project root).
*   **Timestamp Format:** ISO 8601 (e.g., `2026-03-08T14:30:00Z`).
*   **Read State:** `gmail_client.py` reads this to build the `after:{epoch}` Gmail query.
*   **Write State:** `run.py` writes the current UTC time to this file *only* after `append_transactions` and `update_daily_and_monthly` have completed without error.

### 3.3 Data Parsing Robustness
*   **Decoding:** Refine `_decode_body` to correctly extract text from multipart/mixed or HTML-heavy messages.
*   **Parsing:** Continue using the existing OpenAI parser, but with cleaner input from the Gmail client.

## 4. Error Handling
*   **Gmail Failure:** If the API call fails, log the error and skip the run (timestamp remains unchanged).
*   **Parse Failure:** Log specific message IDs that fail parsing but continue with the rest of the batch.
*   **Sheets Failure:** If writing to the sheet fails, the `last_run.txt` will NOT be updated, ensuring the same batch is re-fetched and processed in the next run (idempotency in Sheets will prevent duplicates).

## 5. Success Criteria
*   Only relevant emails are fetched and processed.
*   The system correctly resumes from the last successful run's timestamp.
*   No duplicate transactions are recorded in the Google Sheet.
