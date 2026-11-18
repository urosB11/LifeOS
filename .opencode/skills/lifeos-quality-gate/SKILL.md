---
name: LifeOS Quality Gate
description: Verify a Life OS change before reporting it complete, including tests, migration checks, Git diff review, and honest results.
---

# Life OS Quality Gate

Use before declaring any coding task complete.

## Verification sequence

1. Identify the requirement and acceptance criteria that the change satisfies.
2. Read `pyproject.toml` and README to determine actual available commands; never invent test/lint scripts.
3. Run focused tests first, then the relevant broader suite.
4. If schema changed, test Alembic migration from an empty temporary database and a prior temporary schema where relevant.
5. If frontend changed, test loading, empty, error, keyboard/focus, responsive, and browser console behavior that can be checked in the current environment.
6. Review `git diff --check`, `git status`, and the full diff.
7. Check that no user database, export, backup, `.env`, token, or secret was added.
8. Update impacted docs.

## Report format

Report:

- files changed;
- requirement/behavior covered;
- exact commands executed;
- passed/failed/skipped tests;
- anything not verifiable and why;
- remaining risks or follow-up items.

Never say "all tests pass" unless the tests were actually executed and passed. Never conceal a skipped or failed check.
