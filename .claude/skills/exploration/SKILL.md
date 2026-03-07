---
name: exploration
description: Deep dive into understanding a problem before writing any code. Use at the start of any new feature or significant change. Triggers a structured discovery phase with clarifying questions and scope definition. NO CODE is written during this phase.
disable-model-invocation: true
argument-hint: "[issue ID or feature description]"
---

# /exploration — Deep Problem Understanding

## CRITICAL RULE
**NO CODE IN THIS PHASE. EVER.**

Only: questions, clarifications, trade-off analysis, scope definition.

## Purpose
Understand the problem completely before writing a single line of code. A well-understood problem is 80% solved.

## Step 1: Codebase Context
- Read relevant existing files
- Understand current architecture
- Identify related components and potential conflicts

## Step 2: Ask Clarifying Questions

**Scope**
- What's the minimum viable version?
- What's explicitly OUT of scope?
- Is this a one-time thing or a repeatable pattern?

**UX**
- Who is the user of this feature?
- What is the happy path?
- What are the edge cases?
- What does failure look like to the user?

**Data**
- What data do we need?
- Where does it come from?
- How is it stored? What's the lifecycle?

**Integration**
- What existing systems does this touch?
- What could break?
- Any API dependencies?

**Priority**
- Why now? What's blocked without this?
- What's the cost of NOT doing this?

## Step 3: Produce Exploration Summary

Save to `docs/explorations/[feature-name].md`:

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
1. [Decision] — Options: A, B, C

## Dependencies / Risks
- ...

## Open Questions
- ...

## Ready for Planning?
- [ ] All scope questions answered
- [ ] Data model understood
- [ ] Integration points identified
```

> This phase takes time. Don't rush. The plan is only as good as the exploration.
