# ISSUE-002: End-to-End Integration Test

**ID**: ISSUE-2026-01-19-002  
**Type**: Testing  
**Priority**: P0-Critical  
**Status**: Planned  
**Created**: 2026-01-19  
**Effort**: 2-3 hours

## Summary
Create automated test that validates the complete pipeline from RSS feed ingestion to downloadable video.

## Context
We've tested individual components (RSS, scripts, audio, video) but never the full flow. This is a critical gap before production use.

## Acceptance Criteria
- [ ] Script fetches real RSS feed (TechCrunch AI or similar)
- [ ] Analyzes top article and generates script
- [ ] Creates TTS audio using Google TTS
- [ ] Renders video with subtitles
- [ ] Verifies MP4 file is downloadable from dashboard
- [ ] Logs all costs incurred during test
- [ ] Documents any failures or edge cases

## Implementation Notes
- Use `test_full_pipeline.py` in backend root
- Run against production API (not mocked)
- Should complete in \u003c5 minutes for a 60s video
- Log output to `logs/integration_test.log`

## Dependencies
- Google TTS API enabled
- At least one active RSS feed in database
- Backend and frontend running

## Next Action
**Status**: Ready for implementation
