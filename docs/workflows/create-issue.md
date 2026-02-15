---
description: Capture an idea quickly without breaking flow - formats and logs it as a trackable issue
---

# /create-issue - Quick Idea Capture

## Purpose
Capture an idea immediately without context-switching. The AI formats it and logs it for later exploration.

## How to Use
Simply describe your idea or problem in plain language. Be as rough as you want.

## What I Will Do

1. **Extract the core idea** from your rough description
2. **Categorize it** (Feature, Bug, Improvement, Research, Question)
3. **Assign priority** (P0-Critical, P1-High, P2-Medium, P3-Low)
4. **Create a formatted issue** saved to `/docs/issues/`
5. **Return you to your previous context** immediately

## Issue Template Generated

```markdown
# [Issue Title]

**ID**: ISSUE-YYYY-MM-DD-NNN
**Type**: Feature | Bug | Improvement | Research
**Priority**: P0 | P1 | P2 | P3
**Status**: Captured
**Created**: [timestamp]

## Raw Input
[Your original description]

## Formatted Summary
[1-2 sentence clear description]

## Initial Thoughts
- Potential scope
- Related areas
- Questions to explore

## Next Action
Run `/exploration` on this issue
```

## Example

**You say**: "we should probably have a way to preview the video before it gets finalized, maybe with watermark, so I don't waste TTS credits on bad scripts"

**I generate**:
```markdown
# Video Preview with Watermark Before Finalization

**ID**: ISSUE-2026-01-18-001
**Type**: Feature
**Priority**: P2-Medium
**Status**: Captured

## Raw Input
"we should probably have a way to preview the video before it gets finalized, maybe with watermark, so I don't waste TTS credits on bad scripts"

## Formatted Summary
Add a preview step in the video generation pipeline that renders a draft video with watermark before committing to TTS generation, saving API costs on rejected scripts.

## Initial Thoughts
- Could use free TTS (system voice) for preview
- Watermark indicates "DRAFT - NOT FINAL"
- Approval gate before expensive TTS call
- Affects pipeline flow

## Next Action
Run `/exploration` on this issue
```

---

> [!NOTE]
> This command is about SPEED. Don't overthink. Capture and move on.
