---
description: Execute the implementation plan - write the actual code following the blueprint
---

# /execute - Implementation Mode

## Purpose
Write the actual code, following the approved plan exactly. No improvisation. No scope creep.

## Prerequisites
- [ ] `/exploration` completed
- [ ] `/create-plan` completed  
- [ ] Plan approved by you (Product Owner)
- [ ] Plan file path provided

## How to Use
```
/execute docs/plans/[feature-name].md
```

## Execution Rules

### Rule 1: Follow the Plan
- I implement ONLY what's in the checklist
- If something isn't in the plan, I ask before adding it
- If I discover the plan is wrong, I STOP and discuss

### Rule 2: One Task at a Time
- Complete one checklist item fully before moving to next
- Mark items as complete as I go
- Commit logically after each phase

### Rule 3: No Gold Plating
- Minimum viable implementation first
- Refactoring comes later
- "Working" beats "elegant"

### Rule 4: Document As I Go
- Add inline comments for non-obvious logic
- Update README if needed
- Note any deviations from plan

## Execution Flow

```
┌─────────────────────────────────────────────────────────┐
│                    EXECUTION LOOP                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Read current task from plan.md                       │
│                      │                                   │
│                      ▼                                   │
│  2. Implement the task                                   │
│                      │                                   │
│                      ▼                                   │
│  3. Self-verify it works                                 │
│                      │                                   │
│                      ▼                                   │
│  4. Mark task complete in plan.md                        │
│                      │                                   │
│                      ▼                                   │
│  5. Report progress to you                               │
│                      │                                   │
│                      ▼                                   │
│  6. Next task (or done)                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Progress Reporting

After each phase, I'll report:

```markdown
## Execution Progress: [Feature Name]

### Completed
- [x] Task 1.1 - Created `video_preview.py`
- [x] Task 1.2 - Added preview endpoint

### Current
- [ ] Task 2.1 - Implementing watermark overlay ← WORKING ON THIS

### Remaining  
- [ ] Task 2.2 - Preview UI component
- [ ] Task 3.1 - Integration test

### Issues Found
- None yet / [describe any blockers]

### Time Spent
- Phase 1: ~15 mins
- Phase 2: In progress
```

## When I Stop and Ask

I will pause execution and consult you when:

1. **Ambiguity**: The plan says "implement caching" but doesn't specify where
2. **Conflict**: The plan contradicts existing code
3. **Scope Creep**: I notice we need something not in the plan
4. **Blocker**: An external dependency isn't working
5. **Better Way**: I see a significantly better approach (you decide if we pivot)

## Model Selection Tips

| Task Type | Recommended Model |
|-----------|-------------------|
| Backend logic, APIs | Claude (reasoning) |
| Frontend UI, CSS | Gemini (visual/artistic) |
| Rapid iteration | Cursor Composer (speed) |
| Complex algorithms | Claude or o1 (deep thinking) |
| Fixing bugs | Codex (pattern matching) |

---

## Example Session

**You**: `/execute docs/plans/video-preview.md`

**Me**: 
```
📋 Loading plan: Video Preview with Watermark
📊 Total tasks: 12
📍 Starting Phase 1: Foundation

## Task 1.1: Create preview service module

Creating file: backend/app/services/preview_service.py
```

*[I write the code]*

```
✅ Task 1.1 complete
📝 Created: backend/app/services/preview_service.py (45 lines)

Moving to Task 1.2: Add preview API endpoint
```

---

> [!WARNING]
> If I'm executing and you say "oh also add X" — I will remind you that's scope creep and suggest we capture it as a new issue instead.
