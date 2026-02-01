# Exploration: Phase 2 - RSS Ingestion & Analysis

**Date**: 2026-01-19  
**Status**: Complete ✅  
**Phase**: Planning → Execution

---

## Problem Statement

How do we automatically ingest 50-200 AI news articles daily and use LLM to identify the single most engaging story for video generation, while staying under budget?

---

## Key Questions Explored

### 1. Should we use LLM for content ranking/selection?

**Answer**: ✅ **YES**

**User's Question**: "Are you planning to use LLM to take care of reranking, prioritization, picking up the engaging topic etc?"

**Decision**: LLM will be central to the content selection pipeline.

**Why**:
- Manual curation of 50-200 articles/day is not scalable
- LLM can understand nuance (hype vs substance)
- Cost is acceptable: ~$0.03-0.06/day for scoring new articles
- Enables consistent evaluation across multiple dimensions

---

### 2. What dimensions should we score articles on?

**Answer**: 4 core dimensions with weighted formula

**Scoring Dimensions**:
1. **Relevance** (0-10): How relevant to AI/tech news
2. **Engagement** (0-10): Viral potential, shareability
3. **Recency** (0-10): Time-sensitivity, breaking news
4. **Uniqueness** (0-10): Novel perspective vs rehashed content

**Weighting**:
```
final_score = (
    relevance * 0.3 +
    engagement * 0.4 +  # Highest weight - we want viral potential!
    recency * 0.2 +
    uniqueness * 0.1
)
```

**Rationale**: Engagement weighted highest (40%) because YouTube Shorts success depends on shareability.

---

### 3. Full automation or manual selection?

**Answer**: ⚠️ **Manual selection for MVP**

**Approach**:
- LLM scores and ranks all articles
- Show **top 5** in dashboard UI
- User clicks "Generate Video" on their favorite
- Full automation deferred to post-MVP

**Why Manual for MVP**:
- ✅ Validate LLM's judgment before trusting it fully
- ✅ Editorial control during validation phase
- ✅ Budget control (only generate videos you approve)
- ✅ Learn what scores correlate with good videos

**Future**: Once confident in LLM scoring, enable full automation.

---

### 4. How to handle cost at scale?

**Problem**: 100 articles/day × $0.003/article = $0.30/day = $9/month

**Optimizations**:
1. **Incremental analysis**: Only analyze NEW articles (10-20/day)
   - Cost: ~$0.03-0.06/day = ~$1-2/month
2. **Cache scores**: Don't re-analyze same article
3. **Smart filtering**: Use publish date to skip old content pre-analysis
4. **Batch processing**: Send 10 articles at once to LLM (reduce overhead)

**Target**: $1-2/month for article analysis

---

### 5. Which LLM provider for analysis?

**Answer**: Gemini 2.0 Flash (same as video generation)

**Why**:
- Cheapest: $0.075/$0.30 per 1M tokens
- Fast: Good for batch processing
- Quality: Sufficient for scoring tasks
- Already integrated in Phase 1

**Alternative**: Could use GPT-4o Mini if Gemini quality insufficient

---

### 6. How to ensure article diversity?

**Challenge**: Don't want same topic 5 days in a row

**Solutions** (Post-MVP):
1. **Diversity filter**: Penalize articles on recently covered topics
2. **Topic tracking**: Store `key_topics` in database
3. **Recency decay**: Reduce score of articles on "hot" topics

**For MVP**: Manual selection handles this naturally

---

## Architecture Decisions

### RSS Parsing
**Library**: `feedparser` (Python standard for RSS/Atom)  
**Frequency**: Every 6 hours (4x/day)  
**Deduplication**: URL-based (store in database, check before insert)

### LLM Analysis
**Trigger**: Background task after feed sync  
**Batching**: Process 10 articles at once  
**Caching**: Store scores in database, never re-analyze

### Database Design
**New fields on Article model**:
- Scoring fields (relevance_score, engagement_score, etc.)
- final_score (indexed for fast ranking)
- analyzed_at (track when LLM ran)
- category, key_topics (for future filtering)

### API Design
**Feed endpoints**: CRUD for feed management  
**Article endpoints**: List/filter/analyze/rank  
**Background tasks**: Async feed sync + analysis

---

## Example Flow

1. **Feed Sync** (4x/day):
   ```
   Fetch RSS feeds → Parse entries → Extract metadata → Save to DB
   Result: 50 new articles
   ```

2. **LLM Analysis** (triggered by sync):
   ```
   Fetch unanalyzed articles → Batch into groups of 10 → Send to Gemini
   Response: JSON with scores → Update database
   Result: All articles scored
   ```

3. **User Selection** (daily):
   ```
   GET /api/articles/top → Returns top 5 by final_score
   User picks article → POST /api/articles/{id}/select
   Result: Article marked for video generation
   ```

---

## Cost Breakdown

| Phase | Action | Daily Cost | Monthly Cost |
|-------|--------|------------|--------------|
| Ingestion | RSS parsing | FREE | FREE |
| Analysis | Gemini scoring 20 new articles | $0.06 | $1.80 |
| Selection | UI + manual click | FREE | FREE |
| **Total** | | **$0.06/day** | **$1.80/month** |

Combined with video generation ($3.09/month), **total = $4.89/month** ✅ (under $5 target!)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM scoring inconsistent | Medium | Medium | Manual selection validates quality |
| Feed parsing fails | Low | High | Robust error handling, skip bad feeds |
| Duplicate articles spam DB | Medium | Low | URL-based deduplication |
| Stale/old content ranked highly | Low | Low | Filter by publish_date < 7 days |
| API rate limits (Gemini) | Low | Medium | Batch requests, exponential backoff |

---

## Open Questions

❌ **Answered**:
- ✅ Use LLM for ranking? → Yes
- ✅ Manual or automated selection? → Manual for MVP
- ✅ Which provider? → Gemini Flash
- ✅ How to score? → 4 dimensions, weighted formula
- ✅ Cost acceptable? → Yes, $1.80/month

---

## Dependencies

**From Phase 1** (Already Complete):
- ✅ LLM provider abstraction
- ✅ Gemini provider implementation
- ✅ Database models (Feed, Article)
- ✅ Config management (Pydantic Settings)

**New Libraries Needed**:
- ✅ `feedparser` - Already in requirements.txt
- ✅ `beautifulsoup4` - Already in requirements.txt

---

## Ready for Implementation?

- [x] Approach validated with user
- [x] Architecture decisions made
- [x] Cost model verified
- [x] Dependencies available
- [x] Risks identified

**Status**: ✅ **Ready for `/create-plan` and `/execute`**

---

**Next Step**: Implement Phase 2 as per `phase2_implementation_plan.md`
