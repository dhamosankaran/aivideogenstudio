# ISSUE-2026-01-20-009: Image Cache Cleanup

**Created**: 2026-01-20  
**Priority**: Low  
**Effort**: 5 minutes  
**Status**: Open

---

## Problem

Pexels images are cached in `data/images/` but never cleaned up. Over time, this directory will grow unbounded.

**Current State**:
- Images cached indefinitely
- No size limit
- No automatic cleanup

**Impact**: Low (images are small, ~30KB each, but will accumulate)

---

## Proposed Solution

Add image cleanup to existing `CleanupService`:

```python
# In app/services/cleanup_service.py

def cleanup_images(self, days_to_keep: int = 30) -> Dict[str, int]:
    """Delete cached images older than N days."""
    cutoff = datetime.now() - timedelta(days=days_to_keep)
    deleted = 0
    
    for img_file in Path("data/images").glob("*.jpg"):
        if datetime.fromtimestamp(img_file.stat().st_mtime) < cutoff:
            img_file.unlink()
            deleted += 1
    
    return {"deleted_images": deleted}
```

**Add to cleanup endpoint**:
- Include in `/api/health/cleanup` response
- Run automatically with video/audio cleanup

---

## Acceptance Criteria

- [x] Images older than N days are deleted
- [x] Cleanup included in health endpoint
- [x] Logged in structured format

---

## Estimated Impact

- **Time**: 5 minutes
- **Risk**: None (cached images can be re-downloaded)
- **Value**: Prevents unbounded disk growth
