# Next.js Migration & Regex Parsing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Migrate FinanceTracker from Python/OpenAI/Sheets to a Next.js/Regex/PostgreSQL stack.

**Architecture:** A robust Regex-based "Rule Engine" for transaction parsing, integrated with a Next.js App Router API that fetches Gmail emails and persists them directly to a local PostgreSQL database via Prisma.

**Tech Stack:** Next.js, Prisma, PostgreSQL, googleapis, Regex.

---

### Task 1: Environment & Dependency Cleanup

**Files:**
- Modify: `package.json`
- Delete: `run.py`, `parser.py`, `gmail_client.py`, `sheets_client.py`, `config.py`, `requirements.txt`, `credentials.json`

**Step 1: Remove OpenAI from dependencies**
Run: `npm uninstall openai`

**Step 2: Remove Python files and legacy config**
Run: `rm run.py parser.py gmail_client.py sheets_client.py config.py requirements.txt credentials.json`

**Step 3: Clear Python cache**
Run: `rm -rf __pycache__`

**Step 4: Commit**
```bash
git add package.json package-lock.json
git commit -m "chore: cleanup legacy python files and dependencies"
```

### Task 2: Enhance Gmail Fetching with Recursive Decoding

**Files:**
- Modify: `src/lib/gmail.ts`

**Step 1: Implement recursive MIME decoding**
Add a recursive function `decodeBody(payload)` to `src/lib/gmail.ts` that prioritize `text/plain` then `text/html` (with HTML-to-text stripping).

**Step 2: Refine Search Query**
Update `fetchRecentEmails` to use a more specific query: `newer_than:7d ("spent" OR "debited" OR "charged" OR "paid" OR "payment" OR "transaction" OR "purchased")`.

**Step 3: Commit**
```bash
git add src/lib/gmail.ts
git commit -m "feat: improve gmail body extraction and query filtering"
```

### Task 3: Regex-Based Parser Implementation

**Files:**
- Modify: `src/lib/parser.ts`

**Step 1: Define Regex Rules & Category Map**
Replace OpenAI logic with a `PARSING_RULES` array containing objects with `amount`, `merchant`, and `date` regex patterns.

**Step 2: Implement `parseEmailToTransaction`**
Create the parser function that iterates through rules, extracts values, and assigns categories based on keywords.

**Step 3: Commit**
```bash
git add src/lib/parser.ts
git commit -m "feat: implement regex-based transaction parser"
```

### Task 4: API Sync Route Update

**Files:**
- Modify: `src/app/api/transactions/sync/route.ts`

**Step 1: Remove OpenAI references**
Ensure the route only calls the new `parseEmailToTransaction` (now synchronous).

**Step 2: Robust Error Handling & Idempotency**
Ensure `userId_messageId` uniqueness is checked before insertion.

**Step 3: Commit**
```bash
git add src/app/api/transactions/sync/route.ts
git commit -m "feat: update sync route to use new parser and db storage"
```

### Task 5: Final Verification

**Step 1: Run Build**
Run: `npm run build`
Expected: SUCCESS

**Step 2: Manual Sync Test**
The user can now click the **"Sync Gmail"** button in the UI to verify the migration.
