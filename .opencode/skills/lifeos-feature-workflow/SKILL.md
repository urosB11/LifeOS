---
name: LifeOS Feature Workflow
description: Implement a Life OS feature as a small vertical slice while respecting approved requirements, architecture, roadmap, and user data boundaries.
---

# Life OS Feature Workflow

Use this skill when adding or changing a product feature.

## Procedure

1. Read the relevant sections of `REQUIREMENTS.md`, `ARCHITECTURE.md`, `DATABASE.md`, `SECURITY.md`, and `ROADMAP.md`.
2. Identify the exact requirement IDs and acceptance scenarios affected.
3. Inspect the repository and current Git diff before editing.
4. State the smallest vertical slice: API contract, service rule, persistence change if needed, UI behavior, and tests.
5. Keep the change inside the current authorized roadmap phase.
6. Do not invent product behavior where the documents define a rule. For an unresolved material conflict, stop and report it.
7. Implement only the minimum files needed; do not create speculative abstractions or empty modules.
8. Add tests for normal, invalid, and boundary cases.
9. Run relevant tests and inspect the diff.
10. Update affected documentation and report exact verification results.

## Boundaries

- No external integrations, cloud, AI, or user data transmission in MVP.
- No network exposure beyond `127.0.0.1`.
- No changes to dependencies without stating why.
- Never use the user's real database in tests.
- Never overwrite user changes or make destructive Git operations.
