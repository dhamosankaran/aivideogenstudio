---
name: peer-review
description: Synthesize feedback from other AI models (Cursor, GPT-4, Gemini, Codex) and respond as Lead Developer. Accept valid critiques, reject invalid ones with clear reasoning. Run after /review.
disable-model-invocation: true
---

# /peer-review — The Council of Models

## How to Use
1. Get external reviews from other AI models (Cursor, GPT-4, Gemini, Codex)
2. Copy their feedback
3. Run `/peer-review` and paste the critiques
4. I respond as Lead Developer — accept, reject, or partially address each point

## My Role: Lead Developer

### For Valid Critiques
```markdown
### ✅ ACCEPTED: [Issue Title]
**From**: Codex
**Critique**: [their feedback]
**Assessment**: Valid. [why it's correct]
**Action**: Fixing now.
[code fix]
```

### For Invalid Critiques
```markdown
### ❌ REJECTED: [Issue Title]
**From**: GPT-4
**Critique**: [their feedback]
**Assessment**: Disagree. [clear reasoning]
**Rationale**:
- [reason 1]
- [reason 2]
**Action**: No change.
```

### For Partial Critiques
```markdown
### 🔄 PARTIAL: [Issue Title]
**From**: Gemini
**Critique**: [their feedback]
**Assessment**: Partially valid. [nuance]
**Action**: [what I'll fix and what I won't]
```

## Final Report Format

```markdown
# Peer Review Resolution: [Feature]

## Sources
- Codex: N critiques
- GPT-4: N critiques

## Summary
| Decision | Count |
|----------|-------|
| ✅ Accepted | N |
| ❌ Rejected | N |
| 🔄 Partial | N |

## Detailed Responses
...

## Changes Made
- `file.py:45` — Added error handling
- `component.jsx` — Renamed function

## Ready for Merge?
- [x] All critical issues addressed
- [x] All rejections justified
```

## Model Personalities (for reference)
| Model | Best for |
|-------|----------|
| Codex | Bug finding, edge cases |
| Claude | Architecture, complex logic |
| GPT-4 | Broad security review |
| Gemini | Frontend, UI/UX code |
| Cursor | Quick iterations |

> The goal is not to accept everything. It's a **defensible decision** for every critique. Bad advice should be rejected with clear reasoning.
