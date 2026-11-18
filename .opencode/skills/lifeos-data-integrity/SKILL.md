---
name: LifeOS Data Integrity
description: Safely change Life OS SQLite models, SQLAlchemy mappings, Alembic migrations, relationships, transactions, or activity events.
---

# Life OS Data Integrity

Use for any change to persisted data, ORM models, migrations, relationships, exports, or events.

## Required checks

1. Read `DATABASE.md` and relevant acceptance criteria in `REQUIREMENTS.md`.
2. Inspect current migration history and schema before changing anything.
3. Keep SQLite foreign keys enabled on every connection.
4. Use UUIDv4 string IDs as specified; do not introduce mixed identifier formats.
5. Keep task/project/note relationships and deletion behavior exactly as documented.
6. A note may be unlinked from a deleted task/project but must never be deleted as a side effect.
7. Tag normalization must trim/collapse whitespace, normalize Unicode, and use case-insensitive comparison.
8. Write activity events in the same transaction as the corresponding domain change. Never store note contents or sensitive data in event metadata.
9. Create an Alembic migration for every schema change. Do not rely on `create_all()` for an existing database.
10. Run migration and integrity tests against temporary databases only.

## Required tests

- Valid and invalid foreign keys.
- Duplicate link prevention.
- Project deletion restricted while tasks exist.
- Note preservation when deleting related task/project.
- Note deletion cleans links and tag assignments without deleting shared tags.
- Atomic rollback of domain change and event.
- Export preserves IDs and relationships.

Do not modify a user's real database, manually edit its schema, or perform a destructive data migration without explicit authorization.
