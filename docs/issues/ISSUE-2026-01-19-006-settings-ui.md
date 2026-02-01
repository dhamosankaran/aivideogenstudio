# ISSUE-006: Settings UI (Phase 7)

**ID**: ISSUE-2026-01-19-006  
**Type**: Feature  
**Priority**: P3-Low  
**Status**: Deferred  
**Created**: 2026-01-19  
**Effort**: 4-5 hours

## Summary
Add web UI for managing LLM/TTS provider selection and voice configuration.

## Context
Currently using `.env` file for all configuration. Works well for single-user setup but could be improved with UI.

## Acceptance Criteria
- [ ] Provider selection dropdowns (LLM, TTS)
- [ ] Voice selection from available options
- [ ] Model selection (e.g., gemini-2.0-flash vs gpt-4)
- [ ] Settings saved to database
- [ ] No API key management (stays in `.env`)

## Implementation Notes
- React settings page
- Backend `/api/config` endpoints
- Store preferences in `config` table

## Dependencies
- None

## Next Action
**Status**: Deferred - `.env` approach is working fine
