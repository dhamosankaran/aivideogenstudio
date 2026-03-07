---
name: execute
description: Execute an approved implementation plan. Writes actual code following the blueprint exactly. No improvisation, no scope creep. Run after /create-plan is approved.
disable-model-invocation: true
argument-hint: "[path to approved plan.md, e.g. docs/plans/feature-name.md]"
---

# /execute — Implementation Mode

## Prerequisites
- [ ] `/exploration` completed
- [ ] `/create-plan` completed and approved by Product Owner
- [ ] Plan file path: `$ARGUMENTS`

## Execution Rules

### Rule 1: Follow the Plan
- Implement ONLY what's in the checklist
- If something isn't in the plan, STOP and ask before adding it
- If the plan is wrong, STOP and discuss — don't improvise

### Rule 2: One Task at a Time
- Complete one checklist item fully before moving to the next
- Mark items complete in the plan file as I go
- Commit logically after each phase

### Rule 3: No Gold Plating
- Minimum viable implementation first
- "Working" beats "elegant" at this stage
- Refactoring comes later (or via `/review`)

### Rule 4: Verify File Location
Before creating any new file:
- Confirm the directory matches the file's responsibility
- Routers → `backend/app/routers/`
- Business logic → `backend/app/services/`
- Models → `backend/app/models/` or `backend/app/schemas/`
- Pages → `frontend/src/pages/`
- API clients → `frontend/src/services/`

## Progress Reporting

After each phase:
```
## Progress: [Feature Name]

### Completed
- [x] Task 1.1 — Created backend/app/services/new_service.py

### Current
- [ ] Task 2.1 — Implementing endpoint ← WORKING ON THIS

### Remaining
- [ ] Task 2.2 — Frontend integration

### Blockers
- None / [describe if any]
```

## When I Stop and Ask
1. **Ambiguity** — plan says "add caching" but not where
2. **Conflict** — plan contradicts existing code
3. **Scope Creep** — noticed we need something not in the plan
4. **External Blocker** — dependency not working
5. **Better Way** — significant improvement visible (you decide if we pivot)

> If you say "oh also add X" mid-execution, I will remind you that's scope creep and suggest capturing it as a new issue.
