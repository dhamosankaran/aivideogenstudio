# Single Article URL Scraping Support

**ID**: ISSUE-2026-01-19-001  
**Type**: Feature  
**Priority**: P3-Low  
**Status**: Captured  
**Created**: 2026-01-19

## Raw Input
"Add capability to import individual article URLs (LinkedIn, Medium, personal blogs) in addition to RSS feeds for content ingestion"

## Formatted Summary
Enable users to paste individual article URLs (e.g., LinkedIn posts, Medium articles, blog posts) into the system for content analysis and video generation, complementing the existing RSS feed ingestion pipeline.

## Context
Currently, the system only supports RSS feed URLs for bulk article ingestion. This works well for automation but limits the ability to process specific high-quality articles that users discover manually.

**User Example**: `https://www.linkedin.com/pulse/welcome-january-15-2026-alex-wissner-gross-s0yqe/`

## Initial Thoughts

**Technical Approach**:
- Create `ArticleScraperService` using BeautifulSoup4
- Add `POST /api/articles/import-url` endpoint
- Support 3-5 major platforms initially (Medium, Substack, personal blogs)
- Use generic HTML extraction as fallback

**Challenges**:
- Each site has different HTML structure
- LinkedIn requires authentication (can't scrape)
- Sites frequently change layouts (maintenance burden)
- Anti-scraping measures (rate limits, CAPTCHA)

**Complexity**: High  
**Maintenance**: Ongoing updates needed

## Alternative Approaches

1. **Use official APIs instead of scraping**
   - LinkedIn API, Medium API
   - More reliable but requires API keys
   - May have usage limits

2. **Third-party extraction services**
   - Diffbot, Mercury Parser
   - Costs money but handles all sites
   - No maintenance burden

3. **RSS discovery**
   - Many sites have RSS feeds (even if not obvious)
   - Point users to RSS URL instead of article URL

## Acceptance Criteria

- [ ] User can paste article URL
- [ ] System extracts title, content, author, published date
- [ ] Extracted content flows into normal LLM analysis pipeline
- [ ] Support at least 3 major platforms (Medium, Substack, Ghost)
- [ ] Graceful error handling for unsupported sites
- [ ] Optional: Authentication support for paywalled content

## Dependencies
- Existing: BeautifulSoup4, requests (already installed)
- New: Potentially readability-lxml for better extraction

## Next Action
**Deferred to Post-MVP**

Run `/exploration` when ready to implement. Recommend validating demand first by completing end-to-end video pipeline and seeing if RSS feeds are sufficient.

---

**Captured**: This feature is logged for future consideration but not prioritized for current development cycle.
