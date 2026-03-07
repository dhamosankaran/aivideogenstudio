---
name: review
description: Self-review code for quality, security, correctness, and best practices. Run after implementing a feature, before peer review. Point at a file or say "recent changes".
disable-model-invocation: true
argument-hint: "[file path or 'recent changes']"
---

# /review — Self Code Review

## Review Checklist

### Security
- [ ] No hardcoded secrets/API keys
- [ ] Input validation present at router level
- [ ] No SQL injection risk (ORM parameterizes, no f-strings in raw SQL)
- [ ] Auth checks where needed

### Correctness
- [ ] Logic handles edge cases
- [ ] Error handling is appropriate — no bare `except: pass`
- [ ] Async/await used correctly
- [ ] Resources properly closed/released

### Readability
- [ ] Functions do one thing
- [ ] Variable names are descriptive
- [ ] No magic numbers — use named constants
- [ ] Comments explain "why" not "what"

### Performance
- [ ] No N+1 database queries
- [ ] Appropriate data structures
- [ ] Large data handled efficiently

### Architecture
- [ ] Follows project patterns (routers → services → never reverse)
- [ ] No circular dependencies
- [ ] CSS changes in the correct file (page-specific → page CSS, not ViralNews.css)

## Output Format

```markdown
# Code Review: [file/feature]

## Summary
[One paragraph assessment]

## Findings

### 🔴 Critical: [Title]
**File**: `path/to/file.py:42`
**Issue**: [description]
**Fix**: [suggested fix with code]

### 🟠 Warning: [Title]
...

### 🟡 Suggestion: [Title]
...

## Approved for Peer Review?
- [ ] Yes / No — [reason if no]
```

Severity levels:
- 🔴 Critical — must fix before merge
- 🟠 Warning — should fix, not blocking
- 🟡 Suggestion — nice to have
- 🟢 Note — observation only
