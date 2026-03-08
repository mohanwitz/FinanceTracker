# Finance Tracker Next.js Rewrite Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Completely rewrite the FinanceTracker app into a multi-tenant Next.js (App Router) web application using PostgreSQL, Prisma, NextAuth for Google Login, and the OpenAI API.

**Architecture:** Next.js fullstack application. Frontend uses React, Tailwind CSS, and shadcn/ui. Backend logic is handled via Next.js API Routes. Data is persisted to a PostgreSQL database via Prisma ORM. Authentication handles Google OAuth and requests Gmail read-only scopes to allow fetching emails server-side.

**Tech Stack:** Next.js (App Router), TypeScript, Prisma, PostgreSQL, NextAuth.js (Auth.js v5), Tailwind CSS, shadcn/ui, Googleapis (Node client), OpenAI Node SDK.

---

### Task 1: Project Initialization

**Goal:** Initialize the Next.js project with Tailwind CSS and install necessary dependencies.

**Files:**
- Create: `package.json`
- Create: `tailwind.config.ts`

**Step 1: Scaffold Next.js application**

Run: `npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --force`
Expected: Next.js app created in the current directory.

**Step 2: Install Core Dependencies**

Run: `npm install @prisma/client next-auth@beta googleapis openai @radix-ui/react-icons lucide-react recharts clsx tailwind-merge`
Expected: Dependencies installed successfully.

**Step 3: Install Dev Dependencies**

Run: `npm install -D prisma ts-node @types/node`
Expected: Dev dependencies installed successfully.

**Step 4: Commit**

```bash
git add .
git commit -m "chore: initialize next.js project with core dependencies"
```

---

### Task 2: Database and Prisma Setup

**Goal:** Initialize Prisma, define the database schema, and generate the client.

**Files:**
- Create: `prisma/schema.prisma`
- Create: `src/lib/prisma.ts`

**Step 1: Initialize Prisma**

Run: `npx prisma init`
Expected: `prisma/schema.prisma` and `.env` files created.

**Step 2: Define Prisma Schema**

Modify `prisma/schema.prisma` to include User, Account, Session, VerificationToken, and Transaction models (NextAuth compliant).

**Step 3: Setup Prisma Client Instance**

Create `src/lib/prisma.ts` to export a singleton PrismaClient instance.

**Step 4: Commit**

```bash
git add prisma/schema.prisma src/lib/prisma.ts .env
git commit -m "feat: configure prisma schema for users, accounts, and transactions"
```

---

### Task 3: Authentication Setup (NextAuth)

**Goal:** Configure NextAuth with Google provider to handle login and request Gmail scopes.

**Files:**
- Create: `src/lib/auth.ts`
- Create: `src/app/api/auth/[...nextauth]/route.ts`

**Step 1: Setup NextAuth Configuration**

Create `src/lib/auth.ts` exporting NextAuth handlers using the PrismaAdapter and Google provider (requesting `https://www.googleapis.com/auth/gmail.readonly` scope).

**Step 2: Create API Route for NextAuth**

Create `src/app/api/auth/[...nextauth]/route.ts` to handle NextAuth requests.

**Step 3: Commit**

```bash
git add src/lib/auth.ts src/app/api/auth
git commit -m "feat: setup nextauth with google provider and prisma adapter"
```

---

### Task 4: Gmail Client Setup

**Goal:** Create a utility to fetch the user's OAuth tokens and query the Gmail API.

**Files:**
- Create: `src/lib/gmail.ts`

**Step 1: Create Gmail Fetcher Utility**

Create `src/lib/gmail.ts` with a function `fetchRecentEmails(userId: string)` that retrieves the user's access token from Prisma, initializes the Google OAuth2 client, and fetches recent emails from Gmail.

**Step 2: Commit**

```bash
git add src/lib/gmail.ts
git commit -m "feat: add gmail utility to fetch recent emails using oauth tokens"
```

---

### Task 5: OpenAI Parsing Setup

**Goal:** Create a utility to parse fetched emails into structured transactions using OpenAI.

**Files:**
- Create: `src/lib/parser.ts`

**Step 1: Create OpenAI Parser**

Create `src/lib/parser.ts` with a function `parseEmailToTransaction(subject, body)` that uses the OpenAI SDK to extract JSON data based on a predefined system prompt.

**Step 2: Commit**

```bash
git add src/lib/parser.ts
git commit -m "feat: add openai utility to parse emails into structured json"
```

---

### Task 6: Data Fetching API Route

**Goal:** Create an endpoint that ties the Gmail fetcher and OpenAI parser together to populate the database.

**Files:**
- Create: `src/app/api/transactions/sync/route.ts`

**Step 1: Create Sync API Route**

Create a POST endpoint at `src/app/api/transactions/sync/route.ts` that:
1. Validates the user session.
2. Calls `fetchRecentEmails()`.
3. Iterates over emails, checking if they exist in the DB.
4. Calls `parseEmailToTransaction()` for new emails.
5. Saves parsed transactions to the database using Prisma.

**Step 2: Commit**

```bash
git add src/app/api/transactions/sync/route.ts
git commit -m "feat: create api route to fetch emails and parse transactions"
```

---

### Task 7: Build User Interface (Dashboard & Transactions)

**Goal:** Create the main application view where users can sign in, trigger a sync, and view their transactions.

**Files:**
- Modify: `src/app/page.tsx`
- Create: `src/components/SyncButton.tsx`

**Step 1: Create Sync Button Component**

Create a client component `src/components/SyncButton.tsx` that calls the `/api/transactions/sync` endpoint and handles loading states.

**Step 2: Create the Main Page**

Update `src/app/page.tsx` to:
1. Show a Google Sign-In button if unauthenticated.
2. Fetch the user's transactions from Prisma if authenticated.
3. Render the `SyncButton` and a data table displaying the transactions.

**Step 3: Commit**

```bash
git add src/app/page.tsx src/components/SyncButton.tsx
git commit -m "feat: build dashboard UI with auth, transactions list, and client sync button"
```
