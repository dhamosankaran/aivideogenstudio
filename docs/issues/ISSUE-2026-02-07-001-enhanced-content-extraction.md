# ISSUE-2026-02-07-001: Enhanced Content Extraction (Phase 2)

**Type**: Enhancement  
**Priority**: P2-Medium  
**Status**: Deferred  
**Created**: 2026-02-07

## Summary
Phase 2 enhancements for content extraction to improve reliability and performance.

## Deferred Features

### 1. Gemini URL Context Fallback
When trafilatura fails to extract content, use Gemini's URL Context Tool as fallback.

```python
# Proposed implementation
if not extracted:
    content = await gemini_extract_url(article.url)
```

### 2. Rate Limiting for Blocked Sources
- VentureBeat returns 429 errors
- Add exponential backoff
- Implement per-domain rate limiting

### 3. Background Content Extraction
- Extract content immediately after RSS sync
- Store in database to avoid re-fetching
- Add `extracted_content` column to Article model

### 4. Content Quality Scoring
- Score extracted content quality
- Flag articles with poor extraction
- Priority queue for processing

## Estimated Effort
- Gemini fallback: 2 hours
- Rate limiting: 1 hour  
- Background extraction: 2 hours
- Quality scoring: 1 hour
- **Total**: ~6 hours

## Related
- Phase 1 completed: `content_extractor.py` with trafilatura
- Exploration: `docs/explorations/web-crawling-exploration.md`
