---
description: Self-review code for quality, bugs, and best practices before peer review
---

# /review - Self Code Review

## Purpose
First pass quality check. I review my own code (or code you point me to) with a critical eye before it goes to peer review.

## How to Use
```
/review [file path or "recent changes"]
```

## Review Checklist

### 🔒 Security
- [ ] No hardcoded secrets/API keys
- [ ] Input validation present
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] Auth checks where needed

### 🐛 Correctness
- [ ] Logic handles edge cases
- [ ] Error handling is appropriate
- [ ] No off-by-one errors
- [ ] Async/await used correctly
- [ ] Resources properly closed/released

### 📖 Readability
- [ ] Functions do one thing
- [ ] Variable names are descriptive
- [ ] No magic numbers (use constants)
- [ ] Comments explain "why" not "what"
- [ ] Consistent formatting

### ⚡ Performance
- [ ] No N+1 queries
- [ ] Appropriate data structures used
- [ ] No unnecessary loops
- [ ] Large data handled efficiently
- [ ] Caching where appropriate

### 🧪 Testability
- [ ] Functions are pure where possible
- [ ] Dependencies are injectable
- [ ] Side effects are isolated
- [ ] Test cases exist or are obvious

### 🏗️ Architecture
- [ ] Follows existing patterns in codebase
- [ ] No circular dependencies
- [ ] Proper separation of concerns
- [ ] Doesn't violate DRY excessively

## Review Output Format

```markdown
# Code Review: [file/feature name]

## Summary
[One paragraph overall assessment]

## Severity Levels
- 🔴 **Critical**: Must fix before merge
- 🟠 **Warning**: Should fix, but not blocking
- 🟡 **Suggestion**: Nice to have
- 🟢 **Note**: Observation, no action needed

## Findings

### 🔴 Critical: [Issue Title]
**File**: `path/to/file.py:42`
**Issue**: [description]
**Fix**: [suggested fix]
```python
# Before
bad_code()

# After  
good_code()
```

### 🟠 Warning: [Issue Title]
...

### 🟡 Suggestion: [Issue Title]
...

## Approved for Peer Review?
- [ ] Yes, ready for `/peer-review`
- [ ] No, critical issues must be fixed first
```

---

## Example

**You**: `/review backend/app/services/video_downloader.py`

**Me**:
```markdown
# Code Review: video_downloader.py

## Summary
Generally solid implementation of yt-dlp wrapper. Found one critical issue with unvalidated URLs and a few suggestions for error handling improvements.

## Findings

### 🔴 Critical: URL Not Validated
**File**: `video_downloader.py:23`
**Issue**: User-provided URL passed directly to yt-dlp without validation. Could be exploited for SSRF.
**Fix**: Add URL validation
```python
# Before
def download(url: str):
    ydl.download([url])

# After
def download(url: str):
    if not is_valid_video_url(url):
        raise ValueError("Invalid video URL")
    ydl.download([url])
```

### 🟠 Warning: Silent Exception Swallowing
**File**: `video_downloader.py:45`
**Issue**: Bare `except: pass` hides all errors
**Fix**: Log the error or re-raise specific exceptions

### 🟡 Suggestion: Add Download Progress Callback
**File**: `video_downloader.py:30`
**Issue**: No way to track download progress for UI
**Fix**: Add progress_hook parameter to yt-dlp options

## Approved for Peer Review?
- [ ] No, critical URL validation issue must be fixed first
```

---

> [!NOTE]
> Self-review catches ~60% of issues. Peer review catches the rest. Always do both.
