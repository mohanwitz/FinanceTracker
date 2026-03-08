# Accurate Fetching & Incremental Tracking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve Gmail search accuracy with keywords and ensure robust incremental fetching by updating the last-run timestamp only after successful processing.

**Architecture:**
- **Search Optimization:** Update `config.py` with a keyword-rich `GMAIL_QUERY`.
- **Decoupled State:** Move the `_write_last_run` logic from the Gmail generator to the main orchestrator in `run.py`.
- **Refined Extraction:** Improve HTML/multipart decoding in `gmail_client.py` for better parsing input.

**Tech Stack:** Python 3.10+, Gmail API, Google Sheets API.

---

### Task 1: Update Configuration

**Files:**
- Modify: `/Users/mohan/Projects/FinanceTracker/config.py`

**Step 1: Update GMAIL_QUERY**
Replace the empty or simple query with the keyword-rich one.

```python
# config.py
GMAIL_QUERY = os.getenv("GMAIL_QUERY", '"amount" ("debit" OR "transaction" OR "purchased" OR "alert")').strip()
```

**Step 2: Commit**
```bash
git add config.py
git commit -m "feat: update GMAIL_QUERY with transaction keywords"
```

---

### Task 2: Refine Gmail Client & Decoding

**Files:**
- Modify: `/Users/mohan/Projects/FinanceTracker/gmail_client.py`

**Step 1: Fix imports and typing**
Add `import email.utils` and fix the `_get_credentials` return type hint to handle the union type.

**Step 2: Improve _decode_body**
Ensure it handles multipart/alternative and mixed content more robustly. Remove the `_write_last_run` call from the end of the generator.

**Step 3: Export state management functions**
Make `_read_last_run` and `_write_last_run` public (remove underscore) so `run.py` can use them.

**Step 4: Commit**
```bash
git add gmail_client.py
git commit -m "refactor: improve email decoding and expose state management"
```

---

### Task 3: Update Orchestrator (run.py)

**Files:**
- Modify: `/Users/mohan/Projects/FinanceTracker/run.py`

**Step 1: Update timestamp after successful write**
Import `write_last_run` from `gmail_client` and call it at the end of `main()` only if all steps (fetching, parsing, appending, updating summaries) succeed.

**Step 2: Add logging for the new window**
Log the timestamp being used for the current run.

**Step 3: Commit**
```bash
git add run.py
git commit -m "feat: update last_run timestamp only after successful processing"
```

---

### Task 4: Verification

**Step 1: Run the application**
Run `python run.py` and verify it fetches emails using the new query. Check `last_run.txt` and the logs.

**Step 2: Verify incremental fetch**
Run it again immediately and verify it says "No new messages" or similar, and that `last_run.txt` has updated to the current time.

**Step 3: Final Commit**
```bash
git commit --allow-empty -m "verify: accurate fetching and incremental tracking confirmed"
```
