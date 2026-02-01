---
description: Create a detailed implementation blueprint after exploration - the map for execution
---

# /create-plan - Implementation Blueprint

## Purpose
Transform the exploration findings into a concrete, executable plan. This becomes the "map" that any AI agent can follow.

## Prerequisites
- Must have completed `/exploration` for this feature
- All clarifying questions answered
- Scope locked

## What I Will Generate

A `plan.md` file saved to `/docs/plans/` with this structure:

```markdown
# Plan: [Feature Name]

**Created**: [date]
**Status**: Draft | Approved | In Progress | Complete
**Exploration**: [link to exploration doc]

---

## TL;DR
[2-3 sentences max. What are we building and why?]

---

## Critical Technical Decisions

### Decision 1: [Title]
**Options Considered**:
| Option | Pros | Cons |
|--------|------|------|
| A | ... | ... |
| B | ... | ... |

**Chosen**: Option [X]
**Rationale**: [Why this choice]

### Decision 2: [Title]
...

---

## Architecture Changes

### Files to Create
| File | Purpose |
|------|---------|
| `path/to/file.py` | [what it does] |

### Files to Modify  
| File | Changes |
|------|---------|
| `path/to/existing.py` | [what changes] |

### Data Model Changes
```
[schema or model changes if any]
```

---

## Implementation Checklist

### Phase 1: [Foundation]
- [ ] Task 1.1 - [description]
- [ ] Task 1.2 - [description]

### Phase 2: [Core Logic]
- [ ] Task 2.1 - [description]
- [ ] Task 2.2 - [description]

### Phase 3: [Integration]
- [ ] Task 3.1 - [description]
- [ ] Task 3.2 - [description]

### Phase 4: [Testing & Polish]
- [ ] Task 4.1 - [description]
- [ ] Task 4.2 - [description]

---

## Testing Strategy

### Unit Tests
- [ ] Test [component] - [what to verify]

### Integration Tests
- [ ] Test [flow] - [expected behavior]

### Manual Verification
- [ ] [Step to manually verify]

---

## Rollback Plan
[How do we undo this if it breaks things?]

---

## Open Items
- [ ] [Any remaining questions or blockers]

---

## Approval

- [ ] You (Product Owner) approve scope
- [ ] CTO (me) approve technical approach
- [ ] Ready for `/execute`
```

---

## Plan Quality Checklist

Before the plan is "approved", verify:

- [ ] **Specific**: No vague tasks like "implement feature"
- [ ] **Ordered**: Tasks are in dependency order
- [ ] **Testable**: Each task has clear "done" criteria
- [ ] **Scoped**: No feature creep from exploration
- [ ] **Reversible**: Rollback plan exists

---

## Example

**You**: `/create-plan` for the video preview feature

**I generate**: `docs/plans/video-preview.md`

```markdown
# Plan: Video Preview with Watermark

**Created**: 2026-01-18
**Status**: Draft
**Exploration**: docs/explorations/video-preview.md

---

## TL;DR
Add a preview step that generates a draft video using free system TTS before committing to ElevenLabs. User approves/rejects in the web UI before final generation.

---

## Critical Technical Decisions

### Decision 1: Preview TTS Engine
**Options Considered**:
| Option | Pros | Cons |
|--------|------|------|
| macOS `say` command | Free, instant | Robotic voice |
| pyttsx3 | Cross-platform | Still robotic |
| OpenAI TTS (cheaper tier) | Better quality | Still costs money |

**Chosen**: macOS `say` command
**Rationale**: Zero cost for preview. Quality doesn't matter since it's just for timing/flow review.

...
```

---

> [!TIP]
> A good plan should be readable by a developer who has never seen the codebase. That "developer" might be a future AI agent — or your future self.
