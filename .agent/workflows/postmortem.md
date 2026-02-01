---
description: Analyze AI mistakes and fix the root cause in system prompts or documentation
---

# /postmortem - Learn from AI Mistakes

## Purpose
When I make a mistake, we don't just fix the code — we fix the **system** that caused the mistake. This prevents the same error from happening again.

## How to Use
```
/postmortem [describe what went wrong]
```

## The Analysis Process

### Step 1: Identify the Mistake
What exactly went wrong?

### Step 2: Root Cause Analysis
I ask myself: **"What in my instructions or the project documentation caused this?"**

Possible causes:
- Missing context in CLAUDE.md (system prompt)
- Outdated documentation
- Ambiguous instructions
- Missing workflow step
- Incorrect assumption I made

### Step 3: Fix the System
Update the relevant file:
- `CLAUDE.md` - My system instructions
- `docs/*.md` - Project documentation
- `.agent/workflows/*.md` - Workflow definitions
- Code comments - Inline context

### Step 4: Verify the Fix
Explain how the same situation would be handled correctly now.

---

## Postmortem Template

```markdown
# Postmortem: [Brief Description]

**Date**: [date]
**Severity**: Minor | Moderate | Major
**Detected By**: [you / me / tests]

## What Happened
[Describe the mistake]

## Impact
[What was affected? Time wasted?]

## Root Cause Analysis

### The 5 Whys
1. Why did this happen? → [answer]
2. Why? → [dig deeper]
3. Why? → [dig deeper]
4. Why? → [dig deeper]
5. Why? → [root cause]

### System Gap Identified
[What was missing from instructions/docs?]

## Fix Applied

### Documentation Updated
- **File**: `[path to file]`
- **Change**: [what was added/modified]

```diff
+ Added explicit instruction about X
- Removed ambiguous wording about Y
```

## Prevention
How will this be prevented in the future?

## Verification
[How do we know the fix works?]
```

---

## Example

**You**: 
```
/postmortem

You created a new API endpoint but put it in the wrong folder. You put it in /services instead of /api. This caused imports to fail.
```

**Me**:
```markdown
# Postmortem: Endpoint Created in Wrong Directory

**Date**: 2026-01-18
**Severity**: Minor
**Detected By**: You (import errors)

## What Happened
Created `download.py` endpoint in `backend/app/services/` instead of `backend/app/api/`. This violated the project structure where:
- `/services/` = Business logic (no HTTP)
- `/api/` = HTTP endpoints (routes)

## Impact
- Import errors when running server
- 5 minutes of confusion
- Required file move

## Root Cause Analysis

### The 5 Whys
1. Why wrong folder? → I saw "download" and associated it with the download service
2. Why that association? → The filename was `download.py` like the service
3. Why not check structure? → I didn't re-read the project structure before creating
4. Why? → No reminder in my workflow to verify directory
5. Why? → `/execute` workflow doesn't have a "verify location" step

### System Gap Identified
The `/execute` workflow doesn't remind me to verify file location against the project structure before creating files.

## Fix Applied

### Workflow Updated
- **File**: `.agent/workflows/execute.md`
- **Change**: Added directory verification step

```diff
## Execution Rules

+ ### Rule 0: Verify File Location
+ Before creating any new file:
+ - Check project structure in implementation_plan.md
+ - Confirm directory matches the file's responsibility
+ - API routes → /api/
+ - Business logic → /services/
+ - Data models → /models/
```

### Documentation Updated  
- **File**: `docs/ARCHITECTURE.md`
- **Change**: Added clear directory responsibility table

## Prevention
Now I will check the project structure before every file creation.

## Verification
Next time I create an endpoint, I'll explicitly state:
"Creating in `/api/` because this is an HTTP route, not business logic."
```

---

## When to Run Postmortem

| Situation | Run Postmortem? |
|-----------|-----------------|
| I put code in wrong file/folder | ✅ Yes |
| I used wrong coding pattern | ✅ Yes |
| I misunderstood requirements | ✅ Yes |
| I made a typo | ❌ No (just fix it) |
| External API changed | ❌ No (document the change) |
| You changed your mind | ❌ No (that's normal) |

---

> [!IMPORTANT]
> The goal is not to blame anyone. The goal is to make the **system smarter** so errors don't repeat. Every postmortem should result in a documentation update.
