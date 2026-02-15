# Web Crawling Exploration: Full Article Content Extraction

**Date**: 2026-02-07  
**Purpose**: Evaluate using web crawling to get full article content instead of relying on RSS excerpts for script generation.

---

## Problem Statement

Currently, RSS feeds provide only **partial content** (~2000 characters excerpt). The LLM generates scripts from limited information, which can result in:
- Scripts that miss key details
- Generic or shallow coverage
- LLM "hallucinating" details not in source

**Goal**: Extract full article content to give LLM complete context for better scripts.

---

## Current State: RSS Content Analysis

| Source | Avg Content Length | Content Type |
|--------|-------------------|--------------|
| Ars Technica | ~2000 chars | HTML excerpt with links |
| TechCrunch | ~800 chars | Summary only |
| The Verge | ~1500 chars | Description |
| VentureBeat | ~1000 chars | Summary |
| MIT Tech Review | ~1200 chars | Description |

**Problem**: RSS provides 10-20% of actual article content.

---

## Options for Full Content Extraction

### Option 1: Gemini URL Context Tool (Recommended for Future)

**How it works**: Pass article URLs directly to Gemini API, which fetches and processes content.

```python
# Example API call with URL context
response = model.generate_content(
    contents="Summarize this article for a video script",
    tools=[{"url_context": {"urls": ["https://example.com/article"]}}]
)
```

**Pros**:
- No separate crawling infrastructure
- Handles HTML parsing automatically
- Supports PDFs, images, text
- Reduces our code complexity

**Cons**:
- Newer feature (GA Aug 2025) - may have edge cases
- Extra API cost per URL fetch
- Dependent on Gemini's crawling ability

**Availability**: ✅ Available in Gemini 2.0+

---

### Option 2: Python Web Scraping Library (Recommended for MVP)

**Libraries to use**:
- `trafilatura` - Best for article extraction (handles most news sites)
- `newspaper3k` - Alternative, good for news
- `beautifulsoup4` - Manual parsing if needed

```python
# Example with trafilatura
import trafilatura

def extract_article(url: str) -> str:
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded)
    return text  # Returns clean article text, ~5000-10000 chars
```

**Pros**:
- Runs locally, no API cost
- Full control over extraction
- Fast (< 1 second per article)
- Well-tested on news sites

**Cons**:
- Some sites may block scrapers
- Requires maintenance for edge cases
- Rate limiting concerns

---

### Option 3: Hybrid Approach (Best for Production)

1. **Try Python extraction first** (trafilatura)
2. **Fall back to Gemini URL Context** if extraction fails
3. **Use RSS content as last resort**

```python
async def get_full_content(article_url: str, rss_content: str) -> str:
    # Try local extraction first (free)
    try:
        content = trafilatura.extract(trafilatura.fetch_url(article_url))
        if content and len(content) > 1000:
            return content
    except:
        pass
    
    # Fall back to Gemini URL Context (costs API credits)
    try:
        content = await gemini_extract_url(article_url)
        if content:
            return content
    except:
        pass
    
    # Last resort: use RSS excerpt
    return rss_content
```

---

## Source Crawlability Analysis

Tested crawling each RSS source:

| Source | Crawlable | Notes |
|--------|-----------|-------|
| ✅ Ars Technica | Yes | Full article extracted |
| ✅ TechCrunch | Yes | Full article extracted |
| ⚠️ VentureBeat | Rate Limited | 429 errors, needs delay |
| ✅ The Verge | Yes | Full article extracted |
| ✅ MIT Tech Review | Yes (paywall) | Some articles paywalled |

### Results Summary
- **4/5 sources** are directly crawlable
- **1/5 sources** need rate limiting handling
- Paywall content may require fallback to RSS

---

## Cost Analysis

| Approach | Cost per Article | Notes |
|----------|------------------|-------|
| RSS Only | $0 | Current approach, limited content |
| trafilatura | $0 | Local, no API cost |
| Gemini URL Context | ~$0.001 | Minimal API usage |
| Hybrid | ~$0.0001 | Most use local, few fallback |

---

## Implementation Effort

| Task | Effort | Priority |
|------|--------|----------|
| Add trafilatura to requirements.txt | 5 min | P0 |
| Create `content_extractor.py` service | 2 hours | P0 |
| Integrate with script generation | 1 hour | P0 |
| Add Gemini URL Context fallback | 2 hours | P1 |
| Handle rate limiting for VentureBeat | 1 hour | P2 |
| Store extracted content in DB | 30 min | P1 |

**Total**: ~6-7 hours for full implementation

---

## CTO Recommendation

**Do Phase 1 now.** It's a 2-hour investment that will significantly improve script quality.

The current flow:
```
RSS Feed → Partial Content → LLM → Script (shallow)
```

With extraction:
```
RSS Feed → URL → Full Extraction → LLM → Script (comprehensive)
```
