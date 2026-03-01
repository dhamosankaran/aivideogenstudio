# Exploration: Future Feature Integration Assessment

**Date**: 2026-02-01  
**Status**: CTO Review  
**Requested By**: CEO  

---

## Summary

You've requested three new capabilities:
1. **Viral News Integration** - Pull trending/viral news to Content Library
2. **External Content Paste Flow** - Paste content from Perplexity, LinkedIn, etc. and generate scripts
3. **Financial Market Updates** - Daily updates on gold/silver/copper/bitcoin/stablecoins

This document provides a CTO assessment of each feature: complexity, value, and recommended approach.

---

## 🎯 Current Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                       CONTENT SOURCES                             │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│  RSS Feeds  │   NewsAPI   │   YouTube   │   ??? NEW SOURCES ??? │
│  (existing) │  (existing) │  (Phase 2.5)│                       │
└──────┬──────┴──────┬──────┴──────┬──────┴───────────┬───────────┘
       │             │             │                   │
       v             v             v                   v
┌──────────────────────────────────────────────────────────────────┐
│                      CONTENT LIBRARY                              │
│              Article Model (unified format)                       │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                v
┌──────────────────────────────────────────────────────────────────┐
│                    SCRIPT GENERATION                              │
│              LLM Analysis → Script → Video                        │
└──────────────────────────────────────────────────────────────────┘
```

**Pattern**: All sources ultimately create `Article` objects that flow through the existing pipeline.

---

## Feature 1: Viral News Integration

### What You're Asking For
Pull trending/viral news automatically to supplement the Content Library.

### Available APIs Researched

| API | Coverage | Free Tier | Viral/Trending Features |
|-----|----------|-----------|------------------------|
| **NewsAPI.ai** | 150K+ publishers | Limited | ✅ Virality analysis, event detection |
| **Reddit API** | Reddit only | Free | Trending subreddits via PRAW |
| **Twitter/X Trends API** | Twitter only | Paid/Limited | Trending hashtags by location |
| **Apify Scrapers** | Reddit/Twitter | Pay-per-use | Trend scraping, engagement patterns |
| **Existing NewsAPI** | 80K sources | ✅ Already integrated | Top headlines, but not "viral" ranking |

### CTO Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Complexity** | 🟡 Medium | Need to define "viral" criteria, integrate new API |
| **Maintenance** | 🟢 Low | APIs are stable, no scraping issues |
| **Value** | 🟡 Medium | Already have NewsAPI top headlines |

### The Real Question

> **What makes news "viral" to you?**

Options:
1. **High engagement** - Reddit upvotes, Twitter retweets → Need Reddit/Twitter APIs
2. **Top headlines** - Already have this via NewsAPI `get_top_headlines()`
3. **AI-ranked virality** - Use Gemini to score potential virality → Add to existing analysis

### CTO Recommendation

**Don't add new APIs yet.** Instead:

1. **Quick Win**: Enhance existing NewsAPI integration to:
   - Add "top headlines" source (not just search)
   - Filter by technology/business categories
   - Sort by engagement where data available

2. **Phase 2** (if needed): Add Reddit trending for AI/tech subreddits
   - r/artificial, r/MachineLearning, r/technology
   - Low complexity with PRAW library

**Effort**: 2-3 hours for quick win

---

## Feature 2: External Content Paste Flow

### What You're Asking For
Paste raw text/URLs from Perplexity, LinkedIn, external news sites → Generate video scripts.

### This Is Actually Two Features

| Input Type | Example | Complexity |
|------------|---------|------------|
| **Raw Text Paste** | Copy-paste article text | 🟢 **Easy** |
| **URL Scraping** | Paste LinkedIn URL → scrape content | 🔴 **Hard** |

### Option A: Raw Text Paste (Recommended)

Create a simple "Manual Import" UI where users paste:
- Article title
- Article content (raw text)
- Source URL (optional, for reference)

**How It Works**:
1. User pastes text into a form
2. System creates Article with `source_type="manual"`
3. Normal analysis + script generation flow

**Components Needed**:
- New UI tab: "Manual Import"
- New API endpoint: `POST /api/articles/import-manual`
- Minor Article model update: add `source_type` field

**Effort**: 3-4 hours

### Option B: URL Scraping (Complex)

**Why This Is Hard**:
- LinkedIn: Requires login (blocked)
- Perplexity: JavaScript-heavy rendering
- Medium: Paywall issues
- Each site = custom scraper code

**My Recommendation**: Skip URL scraping. Raw text paste achieves 90% of the goal with 10% of the effort.

### CTO Recommendation

**Build Option A (Raw Text Paste)**:
- User copies article text from any source
- Pastes into our UI
- We process it through existing pipeline

This avoids:
- ❌ Login walls
- ❌ Anti-scraping measures
- ❌ JavaScript rendering
- ❌ Per-site maintenance

**Effort**: 3-4 hours

---

## Feature 3: Financial Market Updates

### What You're Asking For
Daily automated updates on:
- Precious metals: Gold, Silver, Copper
- Crypto: Bitcoin, Stablecoins (USDT, USDC)

### Available Free APIs

| API | Precious Metals | Crypto | Free Tier |
|-----|-----------------|--------|-----------|
| **Metals-API** | ✅ Gold, Silver, Copper | ❌ | 10K calls/month |
| **MetalpriceAPI** | ✅ All metals | ❌ | Free plan |
| **CoinGecko** | ❌ | ✅ All crypto | Generous limits |
| **Gold-API** | ✅ Gold, Silver | ✅ Bitcoin | Limited free |

### Content Type Definition

This is fundamentally different from news articles. This is **market data → narrative generation**.

**Example Output**:
```
📊 Market Update - Feb 1, 2026

Gold: $2,045/oz (+0.8%)
Silver: $23.40/oz (-0.3%)
Bitcoin: $67,500 (+2.1%)
USDT: $1.00 (stable)

Key insight: Gold continues rally amid Fed speculation...
```

### Architecture Decision

**Two Approaches**:

| Approach | Description | Complexity |
|----------|-------------|------------|
| **A: Data → Article** | Fetch prices, generate Article via LLM, flow through pipeline | 🟡 Medium |
| **B: New "Market Update" Flow** | Separate UI/content type for financial content | 🔴 High |

### CTO Recommendation

**Go with Approach A**:

1. Create `MarketDataService` that:
   - Fetches daily prices from Metals-API + CoinGecko
   - Uses Gemini to generate an Article-formatted market summary
   - Creates Article with `content_type="market_update"`

2. Schedule via cron or manual "Refresh Market Data" button

3. Flows through existing Script → Video pipeline

**New Components**:
- `market_data_service.py` - API integration
- API endpoint: `POST /api/market/refresh`
- UI button in Content Library: "Get Market Update"

**Effort**: 4-6 hours

### API Keys Needed
- Metals-API key (free signup)
- CoinGecko API key (free, optional)

---

## Priority Matrix

| Feature | Complexity | Value | Dependencies | CTO Priority |
|---------|-----------|-------|--------------|--------------|
| **Enhanced NewsAPI (viral)** | Low | Medium | None | 🟡 P2 |
| **Raw Text Paste** | Low | High | None | 🔴 P1 |
| **Market Updates** | Medium | Medium | 2 new API keys | 🟡 P2 |

---

## Recommended Implementation Order

### Phase A: Quick Wins (1 week)

1. **Raw Text Paste UI** - 3-4 hours
   - Manual content import for any external source
   - Unblocks Perplexity/LinkedIn use case immediately

2. **NewsAPI Top Headlines** - 2 hours
   - Add "Trending" button to fetch top tech/business news
   - Uses existing NewsAPI integration

### Phase B: Market Data (Week 2)

3. **Market Update Service** - 4-6 hours
   - Metals-API + CoinGecko integration
   - LLM-generated market summary articles

### Phase C: Advanced (Future)

4. **Reddit Trend Integration** - 3-4 hours
   - AI/tech subreddit trending posts
   - Only if Phase A/B features prove insufficient

---

## Questions Before Proceeding

1. **Raw Text Paste**: Is manual copy-paste acceptable, or do you specifically need URL-based scraping?

2. **Market Updates**: 
   - Which specific commodities matter most? (Gold/Silver/Copper as stated?)
   - Which stablecoins? (USDT, USDC, DAI?)
   - Daily or on-demand refresh?

3. **Viral News**: What's your definition of "viral"? 
   - High Reddit engagement?
   - Twitter trending?
   - Just "top headlines"?

4. **Priority**: Given these are all nice-to-haves, which single feature would you want first?

---

## CTO Verdict

**My recommendation**: Start with **Raw Text Paste** as it:
- Unblocks you from depending on any specific source
- Zero API dependencies
- Fastest to implement
- Highest immediate value

Ready to create an implementation plan once you confirm direction.

---

## Feature 4: YouTube & Book Review Enhancements (Immediate)

### Requests
1. **YouTube Download Fixes**: Handle videos without transcripts.
2. **Trim & Create**: Fix broken functionality.
3. **Video Player**: Add option to play video and download (with "no audio/voice" option).
4. **Book Review**: Add book title as text overlay on top.

### Status
- **Priority**: Immediate / Bug Fixes
- **Action**: Assigned to Engineering.

---

## Feature 5: Channel Dashboard — Performance Analytics

### Overview
A dedicated **Channel Dashboard** view within the app to track the performance (views, likes, comments, watch time) of published YouTube Shorts — eliminating the need to switch to YouTube Studio for basic analytics.

### Key Capabilities
1. **YouTube Data API v3 Integration**: Pull video stats (views, likes, comments, subscriber delta) for all uploaded videos via `youtube.videos.list` and `youtube.analytics`.
2. **Per-Video Performance Cards**: Display each published Short with its thumbnail, title, and key metrics (views, likes, CTR, avg watch time).
3. **Trend Graphs**: 7-day / 30-day trend lines for total channel views, subscriber growth, and top-performing Shorts.
4. **Viral Score Indicator**: An at-a-glance metric combining view velocity + like ratio + share count to flag which Shorts are "going viral."
5. **Comparison View**: Side-by-side compare two Shorts to see what title/thumbnail style drives more engagement.

### Technical Notes
- **API Quota**: YouTube Data API has a 10,000 units/day quota. `videos.list` costs 1 unit per call. Batch requests and cache aggressively (poll every 6 hours, not real-time).
- **DB Schema**: New `VideoAnalytics` model with `video_id`, `views`, `likes`, `comments`, `watch_time_hours`, `fetched_at` for historical tracking.
- **Auth**: Requires OAuth 2.0 with `youtube.readonly` scope (already needed for upload flow).

### Status
- **Priority**: Post-Launch / Phase 3
- **Action**: Added to roadmap. Implement after YouTube upload integration is stable.

---

## Feature 6: Human-Centric Visuals & Contextual Grounding

**Date Added**: 2026-02-22  
**CTO Review**: Approved — [Full Assessment](file:///Users/kalaidhamu/.gemini/antigravity/brain/0dd22516-eba1-4db4-a366-1d12ba59916e/implementation_plan.md)

### Goal
Move book review videos beyond abstract metaphors (soldiers, matchsticks) toward realistic human interactions that mirror the engagement of live-action book reviewers.

### Proposed Changes

| # | Proposal | Effort | Impact | Priority |
|---|----------|--------|--------|----------|
| 1 | **Human Presence Weight** — Modify `_build_book_review_script_prompt()` to add a "Human Presence" directive. If script uses personal pronouns (`you`, `I`, `we`), prioritize B-roll of diverse people in relevant settings. Add `human_presence_boost` to `ImageSearchOrchestrator`. | 🟢 Low (2-3h) | 🔴 High | P0 |
| 2 | **Avatar Integration Layer** — Create `avatar_service.py` stub for HeyGen/Synthesia API hooks. Allows overlaying a "talking head" or "book-holding" avatar on cinematic backgrounds. **Note**: Live API adds $0.10-0.50/video cost. | 🟡 Med (6-8h) | 🔴 High | P2 |
| 3 | **Book in 30% of Scenes** — Ensure the physical book or its cover appears in ≥3 of 8 scenes via prompt directives + fallback logic in `enhanced_video_service.py`. | 🟢 Low (1-2h) | 🟡 Med | P0 |
| 4 | **Match-Cut Logic** — Phase A: Add `transition_hint` field to scene schema (fade, cut, match_cut) + variable crossfade durations. Phase B (future): Full FFmpeg `xfade` filter graph for true match-cuts. | 🟢/🔴 Split | 🟡 Med | P1/P2 |

### Files Affected
- `backend/app/prompts/__init__.py` — Prompt engineering for proposals 1, 3, 4a
- `backend/app/services/image_search_orchestrator.py` — Human presence boost parameter
- `backend/app/services/enhanced_video_service.py` — Book fallback logic, transition hints
- `backend/app/services/avatar_service.py` — **New** stub module for proposal 2

### Status
- **Priority**: Future Enhancement
- **Action**: Documented for future sprint. Implement proposals 1, 3, 4a first (prompt-level, ~5 hours), then 2 and 4b.
