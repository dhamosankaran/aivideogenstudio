---
name: postmortem
description: Analyze a mistake to find and fix its root cause in the system — not just the code. Run when an AI error reveals a gap in instructions, documentation, or workflow. Updates CLAUDE.md or docs to prevent recurrence.
disable-model-invocation: true
argument-hint: "[describe what went wrong]"
---

# /postmortem — Fix the System, Not Just the Code

## Purpose
When a mistake happens, don't just fix the code — fix the **system** that caused it. Every postmortem should result in a documentation update that prevents recurrence.

## Process

### Step 1: Identify the Mistake
What exactly went wrong? (`$ARGUMENTS`)

### Step 2: Root Cause — The 5 Whys
Ask "What in the instructions or documentation caused this?"

Possible root causes:
- Missing context in `CLAUDE.md`
- Outdated or stale documentation
- Ambiguous instructions
- Missing step in a workflow skill
- Incorrect assumption

### Step 3: Fix the System
Update the relevant file:
- `CLAUDE.md` — project-wide instruction gap
- `.claude/rules/*.md` — language/path-specific rule gap
- `.claude/skills/*/SKILL.md` — workflow step missing
- `docs/learning.md` — lesson to remember long-term
- Code comments — inline context for future readers

### Step 4: Verify
Explain how the same situation would be handled correctly now.

## Postmortem Template

```markdown
# Postmortem: [Brief Description]

**Date**: [date]
**Severity**: Minor | Moderate | Major
**Detected By**: User | Tests | AI self-correction

## What Happened
[Describe the mistake]

## Impact
[Time wasted, code affected, user impact]

## Root Cause — 5 Whys
1. Why? → [answer]
2. Why? → [dig deeper]
3. Why? → [root cause]

## System Gap
[What was missing from instructions/docs?]

## Fix Applied
**File**: [path]
**Change**: [what was added/modified]

## Prevention
[How this is prevented in the future]

## Verification
[How we know the fix works]
```

## When to Run

| Situation | Run Postmortem? |
|-----------|-----------------|
| Code created in wrong directory | Yes |
| Used wrong coding pattern | Yes |
| Misunderstood requirements | Yes |
| Simple typo | No (just fix it) |
| External API changed | No (document the change) |
| User changed their mind | No (normal product iteration) |
