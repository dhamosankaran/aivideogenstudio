---
description: Deep dive into understanding a problem before writing any code - discovery and clarification phase
---

# /exploration - Deep Problem Understanding

## Purpose
Understand the problem COMPLETELY before writing a single line of code. This phase is about discovery, not implementation.

## ⛔ CRITICAL RULE
**I AM FORBIDDEN FROM WRITING CODE IN THIS PHASE.**

No code snippets. No implementation details. Only:
- Questions
- Clarifications  
- Trade-off analysis
- Scope definition

## How to Use
Point me to an issue (from `/create-issue`) or describe the feature you want to explore.

## What I Will Do

### Step 1: Codebase Context
- Read relevant existing files
- Understand current architecture
- Identify related components

### Step 2: Ask Clarifying Questions
I will ask you questions in these categories:

**Scope Questions**
- What's the minimum viable version of this?
- What's explicitly OUT of scope?
- Is this a one-time thing or a pattern we'll repeat?

**User/UX Questions**  
- Who is the user of this feature?
- What is the happy path?
- What are the edge cases?
- What does failure look like?

**Data Questions**
- What data do we need?
- Where does it come from?
- How is it stored?
- What's the data lifecycle?

**Integration Questions**
- What existing systems does this touch?
- Are there API dependencies?
- What could break?

**Priority Questions**
- Why now? What's blocking without this?
- What's the cost of NOT doing this?

### Step 3: Document Understanding
Create an exploration summary:

```markdown
# Exploration: [Feature Name]

## Problem Statement
[What problem are we solving?]

## User Story
As a [user], I want [goal] so that [benefit].

## Scope
### In Scope
- ...

### Out of Scope  
- ...

### Deferred (Maybe Later)
- ...

## Key Decisions Needed
1. [Decision 1] - Options: A, B, C
2. [Decision 2] - Options: X, Y

## Dependencies
- [What this relies on]

## Risks
- [What could go wrong]

## Open Questions
- [Things still unclear]

## Ready for Planning?
☐ All scope questions answered
☐ Data model understood
☐ Integration points identified
☐ User confirmed understanding
```

---

## Example Session

**You**: `/exploration` - the video preview feature from ISSUE-2026-01-18-001

**Me**: 
Let me understand this better before we plan anything.

1. **Scope**: When you say "preview" - do you mean:
   - (A) See the script text + a rough audio preview?
   - (B) See a full rendered video with placeholder visuals?
   - (C) See exact final video but with watermark?

2. **UX**: Where does this preview happen?
   - In the web UI?
   - As a file you open in VLC?
   - Inline in terminal?

3. **Cost concern**: You mentioned saving TTS credits. What's current cost per video? Is preview worth the complexity or should we just make scripts reviewable first?

4. **Approval flow**: After preview, what's the action?
   - Simple "approve/reject" button?
   - Ability to edit script and regenerate?
   - Iterate indefinitely?

*[I wait for your answers before proceeding]*

---

> [!IMPORTANT]
> This phase takes TIME. Don't rush it. A well-understood problem is 80% solved.
