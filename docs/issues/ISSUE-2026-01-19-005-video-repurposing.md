# ISSUE-005: Video Repurposing (Phase 4)

**ID**: ISSUE-2026-01-19-005  
**Type**: Feature  
**Priority**: P3-Low  
**Status**: Deferred  
**Created**: 2026-01-19  
**Effort**: 6-8 hours

## Summary
Add capability to analyze YouTube videos and generate derivative content using Gemini multimodal.

## Context
Original MVP scope included YouTube URL → transcript → new video. Deferred to validate RSS-based pipeline first.

## Acceptance Criteria
- [ ] Accept YouTube URL input
- [ ] Use Gemini multimodal to analyze video
- [ ] Extract key perspectives and insights
- [ ] Generate derivative script
- [ ] Flow into normal TTS + video pipeline

## Implementation Notes
- Use Gemini 2.0 Flash with video analysis
- No need for yt-dlp or Whisper (Gemini handles it)
- Cost: ~$0.05 per video analysis

## Dependencies
- Gemini API with video analysis enabled

## Next Action
**Status**: Deferred until after 10+ RSS videos generated
