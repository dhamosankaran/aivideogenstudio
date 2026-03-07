---
name: create-plan
description: Transform exploration findings into a concrete, approved implementation blueprint. Run after /exploration. Creates a plan.md file in docs/plans/ that any AI agent can follow to implement the feature.
disable-model-invocation: true
argument-hint: "[feature name or exploration doc path]"
---

# /create-plan — Implementation Blueprint

## Prerequisites
- `/exploration` completed for this feature
- All clarifying questions answered
- Scope locked and agreed

## What I Generate

A `plan.md` file saved to `docs/plans/[feature-name].md`:

```markdown
# Plan: [Feature Name]

**Created**: [date]
**Status**: Draft
**Exploration**: docs/explorations/[feature-name].md

## TL;DR
[2-3 sentences — what we're building and why]

---

## Critical Technical Decisions

### Decision 1: [Title]
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

**Chosen**: Option [X] — **Rationale**: [why]

---

## Architecture Changes

### Files to Create
| File | Purpose |
|------|---------|
| `path/to/new.py` | [what it does] |

### Files to Modify
| File | Changes |
|------|---------|
| `path/to/existing.py` | [what changes] |

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Task 1.1 — [concrete action]
- [ ] Task 1.2 — [concrete action]

### Phase 2: Core Logic
- [ ] Task 2.1 — [concrete action]

### Phase 3: Integration + Testing
- [ ] Task 3.1 — [concrete action]

---

## Rollback Plan
[How to undo if it breaks things]

## Approval
- [ ] Product Owner approves scope
- [ ] CTO (me) approves technical approach
- [ ] Ready for `/execute`
```

## Plan Quality Checklist (before "Approved")
- [ ] Every task is specific — no vague "implement feature"
- [ ] Tasks are in dependency order
- [ ] Each task has a clear "done" criterion
- [ ] No feature creep beyond what was explored
- [ ] Rollback plan exists

> A good plan should be readable by a developer who has never seen the codebase.
