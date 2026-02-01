# ISSUE-2026-01-20-014: Content Strategy & Video Types

**Created**: 2026-01-20  
**Priority**: High  
**Effort**: Planning (0h), Implementation varies  
**Status**: Open

---

## Vision

Build a multi-format AI news channel with diverse content types to engage different audience segments.

---

## Content Types

### 1. Daily AI Updates (Broad Audience)
**Format**: 60-90 second news roundup  
**Frequency**: Daily  
**Target**: General tech audience  
**Sources**: RSS feeds (TechCrunch, VentureBeat, etc.)

**Example Topics**:
- "Top 3 AI News Stories Today"
- "AI Startup Raises $100M"
- "New GPT-5 Features Announced"

**Script Style**: Fast-paced, engaging, accessible

---

### 2. Big Tech Announcements (Deep Dives)
**Format**: 90-120 second focused analysis  
**Frequency**: As needed (2-3x/week)  
**Target**: Tech professionals, enthusiasts  
**Sources**: Company blogs, press releases, tech news

**Example Topics**:
- "OpenAI's GPT-5: What Changed?"
- "Google's Gemini 2.0 Deep Dive"
- "Meta's Llama 3 Breakdown"

**Script Style**: Analytical, detailed, technical

---

### 3. Tech Leader Wisdom (Inspirational)
**Format**: 60 second quote + context  
**Frequency**: 2-3x/week  
**Target**: Aspiring entrepreneurs, students  
**Sources**: Interviews, podcasts, tweets, books

**Example Topics**:
- "Sam Altman on AGI Timeline"
- "Yann LeCun's Take on AI Safety"
- "Andrew Ng's Advice for AI Careers"

**Script Style**: Inspirational, thought-provoking, accessible

---

### 4. arXiv Paper Analysis (Educational)
**Format**: 90-120 second paper summary  
**Frequency**: 1-2x/week  
**Target**: Researchers, students, ML engineers  
**Sources**: arXiv.org (cs.AI, cs.LG, cs.CL)

**Example Topics**:
- "New Transformer Architecture Explained"
- "Breakthrough in Multimodal Learning"
- "Novel Approach to AI Alignment"

**Script Style**: Educational, clear, technical but accessible

---

## Implementation Requirements

### Database Schema
```python
# Add to Article model
content_type: str  # "daily_update", "big_tech", "leader_quote", "arxiv_paper"
source_type: str   # "rss", "manual", "arxiv", "quote"
```

### Content Detection
```python
def classify_content_type(article: Article) -> str:
    """Auto-classify content type based on source and content."""
    
    if "arxiv.org" in article.url:
        return "arxiv_paper"
    
    if any(leader in article.title for leader in ["Sam Altman", "Yann LeCun", ...]):
        return "leader_quote"
    
    if any(company in article.title for company in ["OpenAI", "Google", "Meta", ...]):
        return "big_tech"
    
    return "daily_update"
```

### Script Templates
Different prompt templates for each content type:
- `build_daily_update_prompt()` - Fast-paced, broad
- `build_big_tech_prompt()` - Analytical, detailed
- `build_leader_quote_prompt()` - Inspirational, contextual
- `build_arxiv_paper_prompt()` - Educational, clear

---

## Visual Differentiation

### Thumbnails
- **Daily Updates**: Bright colors, emoji, "TODAY" badge
- **Big Tech**: Company logos, professional, "DEEP DIVE" badge
- **Leader Quotes**: Leader photo, quote text, "WISDOM" badge
- **arXiv Papers**: Academic style, diagrams, "RESEARCH" badge

### End Screens
- **Daily Updates**: "Subscribe for daily AI news!"
- **Big Tech**: "Follow for in-depth analysis!"
- **Leader Quotes**: "Get inspired daily!"
- **arXiv Papers**: "Learn cutting-edge AI!"

---

## Content Calendar Example

| Day | Type | Topic |
|-----|------|-------|
| Mon | Daily Update | "Weekend AI News Roundup" |
| Mon | arXiv Paper | "New Vision Transformer Paper" |
| Tue | Daily Update | "Top AI Stories Today" |
| Tue | Leader Quote | "Sam Altman on AGI" |
| Wed | Daily Update | "Midweek AI Digest" |
| Wed | Big Tech | "Google Gemini 2.0 Analysis" |
| Thu | Daily Update | "AI Funding News" |
| Thu | Leader Quote | "Yann LeCun on AI Safety" |
| Fri | Daily Update | "This Week in AI" |
| Fri | Big Tech | "Meta's Llama 3 Breakdown" |

**Total**: ~10 videos/week

---

## Acceptance Criteria

- [ ] System can classify content types
- [ ] Different script templates for each type
- [ ] Visual differentiation in thumbnails
- [ ] Customized end screens per type
- [ ] Content calendar planning tool

---

## Estimated Impact

- **Audience Growth**: 3-5x (diverse content attracts more viewers)
- **Engagement**: Higher (targeted content for specific interests)
- **Authority**: Established as comprehensive AI news source
