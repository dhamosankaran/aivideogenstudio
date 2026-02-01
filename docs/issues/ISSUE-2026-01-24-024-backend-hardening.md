# Issue: Backend Hardening & Migrations

**Date**: 2026-01-24
**Priority**: 🔴 P0 (Critical Technical Debt)
**Status**: 📋 Planned

## Problem
The database schema is currently updated via manual SQL commands or `Base.metadata.create_all()` which does not handle schema migrations (updates to existing tables). This creates a risk of data loss or schema mismatch (as seen with `app/models.py` drift).

## Validated Solution
Implement **Alembic** for proper database migrations.

## Implementation Plan
1.  **Initialize Alembic**:
    ```bash
    alembic init alembic
    ```
2.  **Configure `alembic.ini`**: Point to `sqlalchemy.url`.
3.  **Configure `env.py`**: Import `app.models.Base` to detect schema changes.
4.  **Create Initial Migration**:
    ```bash
    alembic revision --autogenerate -m "Initial schema snapshot"
    ```
5.  **Verify**: Ensure it captures all Phase 2 columns (`is_selected`, `content_type`, etc.).

## Acceptance Criteria
- [ ] `alembic` command works.
- [ ] Database schema is fully defined in a migration file.
- [ ] Future model changes (e.g. for Phase 3) can be applied via `alembic upgrade head`.
