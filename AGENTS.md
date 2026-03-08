# FinanceTracker - Agent Developer Guidelines

Welcome! This file contains the essential guidelines and context for any AI agents or developers contributing to the FinanceTracker project. Please adhere to these rules strictly to maintain code quality and consistency.

## 1. Project Overview

FinanceTracker is a Python application that fetches transaction emails (e.g., from Gmail), parses them using OpenAI's GPT models to extract structured data (date, amount, merchant, category), and appends the transactions to a Google Sheet. It also updates daily and monthly summaries.

## 2. Build, Lint, and Test Commands

Currently, the project is a lightweight Python script without a complex build system. However, we assume standard Python conventions:

*   **Virtual Environment Setup:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
*   **Running the Application:**
    ```bash
    python run.py
    ```
*   **Linting and Formatting (Recommended):**
    Use `ruff` for fast linting and formatting.
    ```bash
    ruff check .
    ruff format .
    ```
*   **Running Tests:**
    If tests are added, we use `pytest`.
    *   Run all tests: `pytest`
    *   Run a single test file: `pytest tests/test_parser.py`
    *   Run a single test function: `pytest tests/test_parser.py::test_parse_transaction_email`

## 3. Code Style and Conventions

We follow PEP 8 and modern Python conventions.

### 3.1 Python Version and Type Hinting
*   **Python Version:** Assume Python 3.10+ syntax (e.g., use `|` for union types like `str | None` instead of `Optional[str]`).
*   **Type Hints:** Type hints are **mandatory** for all function signatures (arguments and return types) and class attributes.
    *   Use built-in generics (e.g., `list[str]`, `dict[str, Any]`) instead of importing from `typing` where possible.
    *   When using variables whose type is ambiguous, provide an inline type hint.

### 3.2 Code Formatting and Structure
*   **Indentation:** 4 spaces per indentation level.
*   **Line Length:** Max 120 characters is acceptable for better readability, though keeping things concise is preferred.
*   **Docstrings:** Use simple, single-line docstrings for straightforward functions (`"""Does X."""`). Use multi-line docstrings for complex logic.
*   **Dataclasses:** Use `@dataclass` from the `dataclasses` module for data containers (e.g., `ParsedTransaction`). Avoid writing manual `__init__` methods for pure data structures.

### 3.3 Imports
*   **Order:** Group imports in the following order:
    1. Standard library imports (e.g., `import json`, `import logging`).
    2. Third-party imports (e.g., `from openai import OpenAI`).
    3. Local application imports (e.g., `from config import ...`, `from parser import ...`).
*   Separate each group with a blank line.

### 3.4 Naming Conventions
*   **Variables & Functions:** `snake_case` (e.g., `parse_transaction_email`, `message_id`).
*   **Classes:** `PascalCase` (e.g., `ParsedTransaction`).
*   **Constants:** `UPPER_SNAKE_CASE` at the module level (e.g., `SYSTEM_PROMPT`, `TRANSACTION_HEADERS`).
*   **Private Members:** Prefix module-level private functions or class methods with a single underscore (e.g., `_fallback_transaction`, `_sheets_service`).

### 3.5 Error Handling and Logging
*   **No Print Statements:** Use the built-in `logging` module exclusively. Do not use `print()`.
*   **Logger Initialization:** Initialize the logger at the top of each file:
    ```python
    import logging
    logger = logging.getLogger(__name__)
    ```
*   **Exception Handling:**
    *   Catch specific exceptions where possible (e.g., `except json.JSONDecodeError`).
    *   When catching general exceptions, log them using `logger.exception("...")` to automatically capture the stack trace.
    *   Use `logger.warning("...")` or `logger.error("...")` for non-fatal errors that do not require a stack trace.
*   **Fallback Behavior:** When external services (like OpenAI or Gmail) fail, the system should ideally log the failure and either gracefully skip or create a fallback/minimal transaction (see `_fallback_transaction` in `parser.py`).

### 3.6 Data and API Handling
*   **Environment Variables:** All secrets and configuration must be loaded from a `.env` file via `config.py` (e.g., `OPENAI_API_KEY`, `SPREADSHEET_ID`). Never hardcode secrets.
*   **JSON Handling:** Always validate or handle potential parsing errors (`ValueError`, `KeyError`) when interacting with external APIs or JSON text.

## 4. Architectural Patterns

*   **Decoupling:** The project separates concerns into modules: `gmail_client.py` for fetching, `parser.py` for analysis, `sheets_client.py` for storage, and `run.py` as the orchestrator.
*   **Idempotency:** The Sheets client implements idempotency by checking `message_id`s to avoid duplicate entries. Ensure any new write operations account for this to prevent duplicate data.
