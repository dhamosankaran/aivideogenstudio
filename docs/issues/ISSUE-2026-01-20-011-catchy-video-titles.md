# ISSUE-2026-01-20-011: Catchy Video Titles

**Created**: 2026-01-20  
**Priority**: Medium  
**Effort**: 1 hour  
**Status**: Open

---

## Problem

Current video titles are just the article titles, which may not be optimized for YouTube engagement.

**Example**:
- Article: "AI Revolutionizes Video Generation"
- Better: "This AI Creates Videos in 60 Seconds! 🤯"

---

## Proposed Solution

Add LLM-based title generation to script service:

```python
# In app/services/script_service.py

async def generate_catchy_title(
    self,
    article_title: str,
    article_summary: str,
    style: str = "youtube_shorts"
) -> str:
    """Generate engaging YouTube title."""
    
    prompt = f"""
    Create a catchy YouTube Shorts title for this article:
    
    Original Title: {article_title}
    Summary: {article_summary}
    
    Requirements:
    - 60 characters max (YouTube mobile display)
    - Include emotional hook or curiosity gap
    - Use power words (Amazing, Shocking, Secret, etc.)
    - Add relevant emoji (1-2 max)
    - Avoid clickbait (must be accurate)
    
    Style: {style}
    
    Return ONLY the title, nothing else.
    """
    
    title = await self.llm.generate_text(prompt, max_tokens=50)
    return title.strip()
```

---

## Database Changes

```python
# Add to Script model
catchy_title: Optional[str] = Column(String, nullable=True)

# Add to Video model  
youtube_title: Optional[str] = Column(String, nullable=True)
```

---

## Integration Points

1. Generate during script creation
2. Store in database
3. Use for:
   - Thumbnail text
   - YouTube upload metadata
   - Social media posts

---

## Examples

| Original | Catchy |
|----------|--------|
| "AI Startups Raise $100M" | "55 AI Startups Just Raised $100M+ 💰" |
| "New Video Generation Tool" | "This AI Replaced My Video Editor! 🎬" |
| "Metaverse Decline Report" | "The Metaverse is DEAD? 😱" |

---

## Acceptance Criteria

- [ ] LLM generates catchy titles
- [ ] Titles are 60 chars or less
- [ ] Stored in database
- [ ] Used in thumbnail generation
- [ ] Fallback to original title if generation fails

---

## Estimated Impact

- **Time**: 1 hour
- **Cost**: +$0.0001 per video (negligible)
- **Risk**: Low
- **Value**: High (improves click-through rate)
