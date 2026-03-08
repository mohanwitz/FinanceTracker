# Design Doc: Next.js Migration & Regex Parsing

**Date:** 2026-03-08
**Status:** Approved

## Overview
Migrate the FinanceTracker from a Python-based synchronization script (OpenAI + Google Sheets) to a Next.js-based integrated application (Regex + PostgreSQL). This improves performance, reduces costs (no OpenAI), and simplifies the stack.

## Architecture
- **Framework:** Next.js (App Router)
- **Database:** PostgreSQL (via Prisma)
- **Auth:** NextAuth (Google Provider)
- **API:** `/api/transactions/sync` (Route Handler)

## Components

### 1. Gmail Fetching (`src/lib/gmail.ts`)
- **OAuth2:** Use `googleapis` with tokens from the Prisma `Account` table.
- **Decoding:** Implement recursive MIME decoding to handle `text/plain` and `text/html` parts.
- **Filtering:** Use `newer_than:7d` and financial keywords in the search query.

### 2. Regex Parser (`src/lib/parser.ts`)
- **Rule Engine:** A sequence of Regex patterns to extract `amount`, `merchant`, and `date`.
- **CRED Format Support:** Specialized patterns for common CRED transaction alerts.
- **Categorization:** Static mapping of merchant keywords to categories.
- **Fallback:** If parsing fails but keywords suggest a transaction, mark as `needsReview: true`.

### 3. Database Sync (`src/app/api/transactions/sync/route.ts`)
- Fetch emails -> Parse -> Check for duplicates (messageId) -> Save to Prisma.

## Data Flow
1. **Trigger:** `SyncButton.tsx` sends POST to `/api/transactions/sync`.
2. **Fetch:** `fetchRecentEmails` gets raw messages from Gmail API.
3. **Parse:** `parseEmailToTransaction` extracts structured data using Regex.
4. **Persist:** Prisma saves unique transactions to the `Transaction` table.
5. **UI Refresh:** The frontend re-fetches data from the DB.

## Cleanup
- Delete all `.py` files, `__pycache__`, `requirements.txt`, and `credentials.json`.
- Uninstall `openai` package.
- Remove Google Sheets configuration from `.env`.
