# Exploration: Multi-Source Content Ingestion Strategy

**Date**: 2026-01-19  
**Status**: In Progress  
**CTO Review**: Critical architectural decision

---

## Problem Statement

We currently only support **RSS feeds** for content ingestion. User wants to support:
1. **RSS feeds** (✅ already working)
2. **Single article URLs** (e.g., LinkedIn posts, Medium articles)
3. **Video transcripts** (YouTube URLs)

This requires a unified content ingestion strategy that handles multiple source types.

---

## CTO Challenge: Is This the Right Problem?

Before building, let me challenge some assumptions:

### Question 1: What's the actual workflow?

**Option A**: Bulk automated (current approach)
- System fetches RSS feeds daily
- Analyzes 50-200 articles
- Shows top 5
- User picks one

**Option B**: Manual curation
- User finds interesting article/video themselves
- Pastes URL into system
- System analyzes and generates video

**Option C**: Hybrid
- System does bulk RSS analysis (automated)
- User can also paste individual URLs (manual override)

**Which workflow do you actually want?** This determines architecture.

---

### Question 2: What's the quality difference?

**RSS feeds**:
- ✅ Automated, hands-off
- ✅ Multiple sources for diversity
- ❌ Generic, might miss unique content

**Single URLs** (LinkedIn, Twitter, etc.):
- ✅ Specific interesting content you found
- ✅ Unique perspectives
- ❌ Manual effort to find
- ❌ Each site needs custom scraping logic

**Video transcripts**:
- ✅ Repurpose existing content
- ✅ Different format (more engaging?)
- ❌ Requires Gemini multimodal or Whisper
- ❌ Copyright concerns?

**Which sources give you the best content for YouTube Shorts?**

---

### Question 3: What's the MVP scope?

Current status:
- Phase 1: ✅ Provider abstraction
- Phase 2: ✅ RSS ingestion

Remaining phases:
- Phase 3: Script generation
- Phase 4: Video repurposing
- Phase 5: TTS & Audio
- Phase 6: Video composition
- Phase 7: Settings UI
- Phase 8: Dashboard

**Should we add single URL support now, or finish the end-to-end pipeline first?**

My CTO recommendation: **Finish one complete flow before adding input variations.**

---

## Technical Architecture (If We Proceed)

### Option 1: Unified Content Service

**Create**: `ContentIngestionService` that abstracts the source:

```python
class ContentSource(Enum):
    RSS_FEED = "rss"
    ARTICLE_URL = "url"
    VIDEO_TRANSCRIPT = "video"

class ContentIngestionService:
    async def ingest(source: ContentSource, input: str) -> Article:
        if source == RSS_FEED:
            return await self.feed_service.fetch_feed(input)
        elif source == ARTICLE_URL:
            return await self.scraper_service.scrape_article(input)
        elif source == VIDEO_TRANSCRIPT:
            return await self.video_service.analyze_video(input)
```

**Pros**:
- ✅ Single interface for all sources
- ✅ Easy to add new source types
- ✅ Consistent Article model

**Cons**:
- ⚠️ Each source needs different implementation
- ⚠️ Complexity grows with each source type

---

### Option 2: Separate Services (Current Approach)

Keep separate services:
- `FeedService` (already exists)
- `ArticleScraperService` (new)
- `VideoTranscriptService` (new)

**Pros**:
- ✅ Clear separation of concerns
- ✅ Each service can be optimized independently

**Cons**:
- ❌ Duplicate logic for article creation
- ❌ More API endpoints to manage

---

## Implementation Complexity Analysis

### Single Article URL Scraping

**Libraries**:
- `beautifulsoup4` (already installed)
- `requests` or `httpx` (already installed)

**Challenges**:
1. **Each site is different**
   - LinkedIn: Specific HTML structure
   - Medium: Different structure
   - Personal blogs: Varies wildly

2. **Anti-scraping measures**
   - Rate limiting
   - Login walls (LinkedIn!)
   - JavaScript rendering

3. **Maintenance burden**
   - Site changes → scraper breaks
   - Needs constant updates

**Time Estimate**: 2-3 hours per site template

**LinkedIn Specific Issue**: Your example URL likely requires login to view full content!

---

### Video Transcript Analysis

**Already Built**: Gemini multimodal in Phase 1!

```python
# This already works from Phase 1:
gemini = ProviderFactory.create_llm_provider(LLMProvider.GEMINI)
transcript = await gemini.analyze_video(
    video_url="https://youtube.com/watch?v=...",
    prompt="Extract key points from this video"
)
```

**Complexity**: ✅ **Low** - just wire up to Article creation

**Cost**: Same as article analysis (~$0.003 per video)

---

## CTO Recommendations

### Recommendation 1: Finish Core Pipeline First 🎯

**Why**:
- You don't have a working end-to-end flow yet
- No point optimizing input if you can't generate output
- Can validate with RSS feeds, then add sources

**Action**:
- Complete Phases 3-6 (Script → Video generation)
- Then come back to input diversity

---

### Recommendation 2: Video Transcripts Are Easy Wins 🎬

**Why**:
- Already have Gemini multimodal (Phase 1)
- Just need to wire it up
- No scraping complexity

**Action**:
- Add `POST /api/articles/import-video` endpoint
- Uses existing Gemini provider
- Maps transcript → Article model

**Time**: ~1 hour

---

### Recommendation 3: Single URLs Are High Maintenance ⚠️

**Why**:
- Each site needs custom scraper
- LinkedIn requires login (won't work)
- Breaks when sites change

**Alternative**:
- Use RSS feeds instead (every site has one)
- Or use API integrations (LinkedIn API, Twitter API)

**Action**:
- Skip for MVP
- Add only if user validates demand

---

## Decision Matrix

| Source Type | Complexity | Maintenance | Value | CTO Vote |
|-------------|-----------|-------------|-------|----------|
| **RSS Feeds** | Low | Low | High | ✅ Keep |
| **Video Transcripts** | Low | Low | High | ✅ Add Next |
| **Single URLs** | High | High | Medium | ❌ Defer |

---

## Proposed Phasing

### Phase 2.5 (Optional): Video Import
**If you want video transcript support now:**
- [ ] Create `POST /api/articles/import-video` endpoint
- [ ] Use Gemini multimodal to get transcript
- [ ] Extract key points, create Article
- [ ] Trigger normal LLM analysis flow

**Time**: 1 hour  
**Value**: High (repurpose existing videos)

### Post-MVP: Single URL Support
**Only if user validates need:**
- [ ] Build generic article scraper
- [ ] Support 2-3 major sites (Medium, Substack)
- [ ] Skip sites requiring login (LinkedIn, Twitter)

**Time**: 4-6 hours  
**Value**: Medium (nice-to-have)

---

## Questions for User

Before I proceed, I need to know:

1. **Primary use case**: Are you finding articles manually (paste URLs) or letting the system find them (RSS automation)?

2. **Video transcripts**: Do you want to repurpose YouTube videos into Shorts? (Easy to add)

3. **LinkedIn URL**: That specific link likely requires login. Do you have other public article URLs?

4. **Priority**: Should we finish the end-to-end pipeline (Phases 3-6) before adding input variations?

---

## CTO Decision

**My recommendation**: 

✅ **Do this**:
1. Finish Phases 3-6 (complete one video end-to-end)
2. Add video transcript support (Phase 2.5)
3. Test with RSS + YouTube, validate quality

❌ **Defer this**:
1. Single article URL scraping (high maintenance, moderate value)
2. Can add later if demand is proven

**Rationale**: Better to have one complete, working pipeline than three half-built input methods.

---

**What's your call?** Should I:
- **A**: Continue to Phase 3 (Script Generation) and finish the pipeline
- **B**: Add video transcript support now (1 hour, easy win)
- **C**: Build single URL scraper despite challenges

I'll follow your decision, but as CTO, I'm pushing for **A** or **B**.
