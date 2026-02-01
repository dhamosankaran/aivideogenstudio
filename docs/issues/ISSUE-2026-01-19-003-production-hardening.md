# ISSUE-003: Production Hardening

**ID**: ISSUE-2026-01-19-003  
**Type**: Infrastructure  
**Priority**: P0-Critical  
**Status**: Planned  
**Created**: 2026-01-19  
**Effort**: 4-6 hours

## Summary
Add error recovery, monitoring, and resource management to make the system production-ready.

## Context
Current implementation has no retry logic, limited logging, and no resource cleanup. This will cause failures in daily production use.

## Acceptance Criteria

### Error Recovery
- [ ] Retry logic for API failures (3 retries, exponential backoff)
- [ ] Graceful degradation (save partial progress on failure)
- [ ] Database transaction rollbacks for failed operations
- [ ] Circuit breaker for repeated API failures

### Monitoring & Logging
- [ ] Structured JSON logging with timestamps
- [ ] Real-time cost tracking (log every API call)
- [ ] `/api/health/detailed` endpoint (DB, disk, API status)
- [ ] Error aggregation (count failures by type)

### Resource Management
- [ ] Disk space monitoring (alert if \u003c1GB free)
- [ ] Auto-cleanup old videos (keep last 30 days)
- [ ] Background task queue status endpoint
- [ ] Memory usage tracking

## Implementation Notes
- Use Python `tenacity` library for retries
- Use `structlog` for structured logging
- Add `psutil` for system monitoring
- Store logs in `logs/` directory with rotation

## Dependencies
- None (pure backend work)

## Next Action
**Status**: Ready for implementation
