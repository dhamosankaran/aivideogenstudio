---
name: create-issue
description: Capture an idea, feature request, or bug quickly without breaking flow. Formats and saves it as a trackable issue in docs/issues/. Use when someone says "we should add X", "I noticed Y is broken", or wants to log an idea for later.
disable-model-invocation: true
argument-hint: "[describe the idea or problem in plain language]"
---

# /create-issue — Quick Idea Capture

## Purpose
Capture an idea immediately without context-switching. Format it and log it for later exploration. Speed is the goal — capture and move on.

## How to Use
```
/create-issue we should add video preview before finalizing so I don't waste TTS credits
```
Or just describe the idea in plain language after invoking.

## What I Will Do

1. **Extract the core idea** from the rough description (`$ARGUMENTS`)
2. **Categorize**: Feature | Bug | Improvement | Research | Question
3. **Assign priority**: P0-Critical | P1-High | P2-Medium | P3-Low
4. **Determine next issue number** by reading `docs/issues/README.md`
5. **Create formatted issue** saved to `docs/issues/ISSUE-YYYY-MM-DD-NNN-slug.md`
6. **Update** `docs/issues/README.md` with the new entry
7. **Return you to your previous context** immediately

## Issue Template Generated

```markdown
# [Issue Title]

**ID**: ISSUE-YYYY-MM-DD-NNN
**Type**: Feature | Bug | Improvement | Research
**Priority**: P0 | P1 | P2 | P3
**Status**: Captured
**Created**: [timestamp]

## Raw Input
[Original description]

## Formatted Summary
[1-2 sentence clear description]

## Initial Thoughts
- Potential scope
- Related areas
- Questions to explore

## Next Action
Run `/exploration` on this issue when ready.
```

> Speed is the goal. Don't overthink. Capture and move on.
