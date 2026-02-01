---
description: Multi-model peer review - synthesize feedback from other AI models and address or defend
---

# /peer-review - The Council of Models

## Purpose
Use multiple AI models to review code, then synthesize their feedback. I act as the **Lead Developer** who must either fix issues or explain why the feedback is wrong.

## The Process

```
┌─────────────────────────────────────────────────────────┐
│                    PEER REVIEW FLOW                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Step 1: You get reviews from other models               │
│          (Codex, Cursor, GPT-4, Gemini, etc.)           │
│                      │                                   │
│                      ▼                                   │
│  Step 2: Paste their critiques to me                     │
│                      │                                   │
│                      ▼                                   │
│  Step 3: I analyze as Lead Dev                           │
│          - Accept valid critiques → Fix them             │
│          - Reject invalid critiques → Explain why        │
│                      │                                   │
│                      ▼                                   │
│  Step 4: Report final decision                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## How to Use

1. **Get External Reviews**: Take the code to other AI models and ask them to review it
2. **Collect Critiques**: Copy their feedback
3. **Run**: `/peer-review` and paste the critiques
4. **I Respond**: As Lead Dev, I'll address each point

## My Role: Lead Developer

When you paste critiques, I will respond to each one with:

### For Valid Critiques
```markdown
### ✅ ACCEPTED: [Issue Title]
**From**: Codex
**Critique**: "The error handling in line 45 silently swallows exceptions"
**Assessment**: Valid concern. This could hide bugs in production.
**Action**: Fixing now.

```python
# Fix applied
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise
```
```

### For Invalid Critiques
```markdown
### ❌ REJECTED: [Issue Title]
**From**: GPT-4
**Critique**: "You should use a class instead of a function here"
**Assessment**: Disagree. This is a simple stateless operation. A class would add unnecessary complexity. The function pattern is correct here.
**Rationale**: 
- No state to manage
- Single responsibility  
- Easier to test
- Follows existing codebase patterns
**Action**: No change.
```

### For Partially Valid Critiques
```markdown
### 🔄 PARTIAL: [Issue Title]
**From**: Gemini  
**Critique**: "Add more comments throughout the code"
**Assessment**: Partially valid. Some complex logic needs explanation, but over-commenting simple code reduces readability.
**Action**: Adding comments only to non-obvious logic (lines 23-35, 67-72).
```

## Model Personalities (For Your Reference)

Use these models strategically:

| Model | Personality | Best For |
|-------|-------------|----------|
| **Codex** | Grumpy senior dev, fixes silently | Bug finding, edge cases |
| **Claude** | Communicative lead, explains reasoning | Architecture, complex logic |
| **GPT-4** | Generalist, sometimes over-engineers | Broad review, security |
| **Gemini** | Artistic, visual-focused | Frontend, UI/UX code |
| **Cursor** | Fast, pragmatic | Quick iterations |

## Final Report Format

```markdown
# Peer Review Resolution: [Feature Name]

## Review Sources
- Codex: 3 critiques
- GPT-4: 5 critiques  
- Gemini: 2 critiques

## Summary
| Decision | Count |
|----------|-------|
| ✅ Accepted | 4 |
| ❌ Rejected | 3 |
| 🔄 Partial | 3 |

## Detailed Responses

### ✅ ACCEPTED: [Issue 1]
...

### ❌ REJECTED: [Issue 2]
...

## Code Changes Made
- `file1.py`: Added error handling (lines 45-50)
- `file2.py`: Fixed edge case in validation

## Ready for Merge?
- [x] All critical issues addressed
- [x] Rejections justified
- [x] Tests passing
```

---

## Example Session

**You**: 
```
/peer-review

Here's what Codex said:
"Line 34 has a potential null pointer. Line 67 uses deprecated API."

Here's what GPT-4 said:
"You should add TypeScript instead of JavaScript. Also the function names aren't descriptive enough."
```

**Me**:
```markdown
# Peer Review Resolution: Video Downloader

## Detailed Responses

### ✅ ACCEPTED: Potential Null Pointer (Codex)
**Assessment**: Valid. If API returns null, we'd crash.
**Action**: Adding null check.
```python
result = api_call()
if result is None:
    raise ValueError("API returned no data")
```

### ✅ ACCEPTED: Deprecated API (Codex)  
**Assessment**: Valid. `yt_dlp.download()` signature changed in v2024.
**Action**: Updating to new API.

### ❌ REJECTED: Add TypeScript (GPT-4)
**Assessment**: Out of scope. This is a Python backend project. TypeScript suggestion is irrelevant.
**Action**: No change.

### 🔄 PARTIAL: Function Names (GPT-4)
**Assessment**: Partially valid. `do_thing()` is vague, but `download_video()` is already clear.
**Action**: Renaming only `do_thing()` → `extract_audio_from_video()`.
```

---

> [!IMPORTANT]
> The goal is not to accept everything. It's to have a **defensible decision** for every critique. Bad advice should be rejected with clear reasoning.
