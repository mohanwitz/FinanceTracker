# Transaction Email Finance Tracker

A local Python app that runs on a schedule (cron), reads transaction emails from Gmail, uses OpenAI to parse and categorize spending, and writes day-wise and month-wise data to Google Sheets.

## Architecture

1. **Cron** runs the script daily (or at your chosen time).
2. **Gmail API** fetches unread or label-based transaction emails.
3. **Parser** extracts text from each email; **OpenAI** returns structured fields (date, amount, merchant) and category.
4. **Google Sheets API** appends transactions and updates daily/monthly summaries.

## Prerequisites

- Python 3.10+
- Google Cloud project with Gmail API and Google Sheets API enabled
- OpenAI API key
- A Google Sheet with three sheets: **Transactions**, **Daily**, **Monthly**

## One-time setup

1. **Google Cloud Console**
   - Create a project (or use existing).
   - Enable **Gmail API** and **Google Sheets API**.
   - Create OAuth 2.0 credentials (Desktop app).
   - Download and save as `credentials.json` in the project root.

2. **OpenAI**
   - Get an API key from [platform.openai.com](https://platform.openai.com) and add it to `.env`.

3. **Google Sheet**
   - Create a new spreadsheet.
   - Add three sheets named: `Transactions`, `Daily`, `Monthly`.
   - Copy the spreadsheet ID from the URL: `https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit`

4. **Environment**
   - Copy `.env.example` to `.env` and fill in `OPENAI_API_KEY`, `SPREADSHEET_ID`, and optionally `GMAIL_LABEL` / `GMAIL_QUERY`.

5. **First run (OAuth)**
   - Run once interactively to complete Google OAuth and generate `token.json`:
   ```bash
   python run.py
   ```
   - Complete the browser flow; `token.json` will be created.

## Installation

```bash
cd /path/to/FinanceTracker
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

- **Manual**: `python run.py`
- **Scheduled (cron)**: Add a line to your crontab, e.g. daily at 8 AM:
  ```bash
  0 8 * * * cd /Users/mohan/Projects/FinanceTracker && .venv/bin/python run.py >> finance_tracker.log 2>&1
  ```
  Adjust the path and venv location for your system.

## Config

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required. OpenAI API key. |
| `SPREADSHEET_ID` | Required. Google Sheet ID. |
| `GMAIL_LABEL` | Optional. Gmail label to filter (e.g. `finance/transactions`). |
| `GMAIL_QUERY` | Optional. Gmail search query (e.g. `from:alerts@bank.com`). |

The app uses "since last run" by default: it stores the last run time and only fetches Gmail messages after that time on the next run.

## Data model

- **Transactions** sheet: one row per transaction (email_date, transaction_date, amount, merchant, category, raw_subject, message_id).
- **Daily** sheet: one row per day with total and per-category sums.
- **Monthly** sheet: one row per month with total and per-category sums.

Categories are fixed (Food & Dining, Transport, Shopping, Bills, Entertainment, Health, Other) so summaries stay consistent.

## Logs

Logs are written to `finance_tracker.log` in the project directory (and to stdout when run manually).
