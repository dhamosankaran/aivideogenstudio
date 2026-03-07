"""
Daily AI Digest service.

Handles LLM-based article ranking and digest article creation
for the multi-story roundup video format.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Article
from app.services.provider_factory import ProviderFactory, LLMProvider

logger = logging.getLogger(__name__)


def _utcnow():
    return datetime.now(timezone.utc)


class DailyDigestService:
    """
    Handles article ranking and digest article creation.

    Ranking uses a single batched LLM call across all selected articles.
    Digest article stores stories as key_points JSON so ScriptService
    can pass them directly to _build_daily_digest_script_prompt().
    """

    def __init__(self, db: Session):
        self.db = db
        self.llm = ProviderFactory.create_llm_provider(provider=LLMProvider.GEMINI)

    # ── Public API ─────────────────────────────────────────────────────

    async def rank_articles(self, article_ids: List[int]) -> List[dict]:
        """
        Rank a list of articles by AI relevance and impact.

        Single batched LLM call — not N individual calls.
        Falls back to recency sort if LLM fails.

        Returns list of dicts:
          {article_id, rank, title, source, company, key_fact, impact,
           impact_score, rank_reason, headline_suggestion}
        """
        articles = (
            self.db.query(Article)
            .filter(Article.id.in_(article_ids))
            .all()
        )

        if not articles:
            raise ValueError("No articles found for the given IDs")

        # Build ranking prompt
        prompt = self._build_ranking_prompt(articles)

        try:
            response_text = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.2,
                max_tokens=2000,
                response_mime_type="application/json",
            )
            ranked = self._parse_ranking_response(response_text, articles)
            logger.info(f"[DailyDigest] Ranked {len(ranked)} articles via LLM")
            return ranked

        except Exception as e:
            logger.warning(f"[DailyDigest] LLM ranking failed, falling back to recency: {e}")
            return self._recency_fallback(articles)

    async def create_digest_article(
        self,
        ranked_article_ids: List[int],
        title: str,
        ranked_metadata: Optional[List[dict]] = None,
    ) -> Article:
        """
        Create a single Article record aggregating N source articles.

        The Article flows into the existing script → audio → video pipeline.
        Stories are stored in key_points so ScriptService can access them.
        """
        source_articles = (
            self.db.query(Article)
            .filter(Article.id.in_(ranked_article_ids))
            .all()
        )

        # Sort by the caller-supplied order (ranked_article_ids order = rank order)
        id_to_article = {a.id: a for a in source_articles}
        ordered = [id_to_article[aid] for aid in ranked_article_ids if aid in id_to_article]

        # Build stories list for key_points (used by script prompt)
        stories = []
        for i, article in enumerate(ordered):
            meta = {}
            if ranked_metadata:
                meta = next((m for m in ranked_metadata if m.get("article_id") == article.id), {})

            feed_name = ""
            if article.feed:
                feed_name = article.feed.name
            elif article.viral_news_source:
                feed_name = article.viral_news_source.source_name or "NewsAPI"

            stories.append({
                "title": article.title,
                "source": feed_name,
                "company": meta.get("company", _extract_company(article.title)),
                "key_fact": meta.get("key_fact", article.description or ""),
                "impact": meta.get("impact", ""),
                "description": article.description or "",
                "rank": i + 1,
            })

        # Unique synthetic URL for the digest
        digest_uid = str(uuid.uuid4())[:8]
        today = _utcnow().strftime("%Y%m%d")
        digest_url = f"digest://{today}-{digest_uid}"

        # Summary from title + story count
        story_titles = "; ".join(s["title"][:60] for s in stories[:3])
        summary = f"Daily AI digest covering {len(stories)} stories: {story_titles}"

        article = Article(
            title=title,
            url=digest_url,
            suggested_content_type="daily_update",
            content=json.dumps({"stories": stories}),
            summary=summary,
            key_points=stories,  # ScriptService reads this for prompt
            is_processed=True,
            is_selected=True,
            published_at=_utcnow(),
            created_at=_utcnow(),
        )

        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        logger.info(f"[DailyDigest] Created digest article {article.id}: '{title}' ({len(stories)} stories)")
        return article

    def list_digest_articles(self, limit: int = 20) -> List[Article]:
        """List existing digest articles (most recent first)."""
        return (
            self.db.query(Article)
            .filter(Article.suggested_content_type == "daily_update")
            .filter(Article.url.like("digest://%"))
            .order_by(Article.created_at.desc())
            .limit(limit)
            .all()
        )

    # ── Private helpers ────────────────────────────────────────────────

    def _build_ranking_prompt(self, articles: List[Article]) -> str:
        articles_text = ""
        for i, article in enumerate(articles):
            feed_name = ""
            if article.feed:
                feed_name = article.feed.name
            elif hasattr(article, "viral_news_source") and article.viral_news_source:
                feed_name = getattr(article.viral_news_source, "source_name", "") or ""

            articles_text += f"""
Article {article.id}:
  Title: {article.title}
  Source: {feed_name}
  Description: {(article.description or '')[:200]}
  Published: {article.published_at or 'unknown'}
"""

        return f"""You are an AI news editor ranking articles for a daily YouTube Shorts digest targeted at tech-savvy AI enthusiasts.

## ARTICLES TO RANK
{articles_text}

## RANKING CRITERIA (score each 1-10):
- impact: How significant is this for the AI field? (model launches, policy, funding = high; opinion = low)
- novelty: Is this genuinely new/unexpected vs incremental? (surprises score high)
- ai_relevance: How directly related to AI/ML? (AI-native = 10, tangentially related = low)
- audience_value: Will @realAIInsider followers care? (practical implications score high)

## OUTPUT FORMAT (strict JSON array):
[
  {{
    "article_id": <int>,
    "rank": <int starting from 1>,
    "impact_score": <float 1-10>,
    "company": "<primary company or topic name, e.g. 'OpenAI', 'Google DeepMind', 'US AI Policy'>",
    "key_fact": "<the single most important fact in under 15 words>",
    "impact": "<why this matters to AI practitioners in under 12 words>",
    "rank_reason": "<1 sentence explaining why this article ranked here>",
    "headline_suggestion": "<punchy 8-word YouTube Short headline>"
  }},
  ...
]

Rank ALL {len(articles)} articles. Rank 1 = most important. Output only the JSON array, no other text."""

    def _parse_ranking_response(self, response_text: str, articles: List[Article]) -> List[dict]:
        """Parse LLM ranking response into a clean list."""
        import re

        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?", "", response_text).strip()

        try:
            ranked = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON array in the response
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if match:
                ranked = json.loads(match.group(0))
            else:
                raise ValueError(f"Cannot parse ranking JSON: {text[:200]}")

        # Enrich with article title for convenience
        id_map = {a.id: a for a in articles}
        result = []
        for item in ranked:
            article_id = item.get("article_id")
            article = id_map.get(article_id)
            if article:
                item["title"] = article.title
                item["description"] = article.description or ""
                result.append(item)

        result.sort(key=lambda x: x.get("rank", 999))
        return result

    def _recency_fallback(self, articles: List[Article]) -> List[dict]:
        """Sort by published_at DESC if LLM ranking fails."""
        sorted_articles = sorted(
            articles,
            key=lambda a: a.published_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
        result = []
        for i, article in enumerate(sorted_articles):
            feed_name = ""
            if article.feed:
                feed_name = article.feed.name

            result.append({
                "article_id": article.id,
                "title": article.title,
                "description": article.description or "",
                "rank": i + 1,
                "impact_score": 5.0,
                "company": _extract_company(article.title),
                "key_fact": (article.description or "")[:120],
                "impact": "",
                "rank_reason": "Ranked by recency (LLM ranking unavailable)",
                "headline_suggestion": article.title[:60],
            })
        return result


def _extract_company(title: str) -> str:
    """
    Simple heuristic: extract the first capitalized word sequence
    that looks like a company or product name from the title.
    """
    known = [
        "OpenAI", "Google", "Anthropic", "Meta", "Apple", "Microsoft",
        "Nvidia", "Alibaba", "DeepMind", "Gemini", "ChatGPT", "Claude",
        "Grok", "Mistral", "Cohere", "xAI", "Tesla", "Amazon", "AWS",
        "ByteDance", "Baidu", "Tencent", "Samsung", "Huawei",
    ]
    for name in known:
        if name.lower() in title.lower():
            return name
    # fallback: first two title-case words
    words = title.split()
    candidates = [w for w in words[:5] if w[0].isupper() and len(w) > 2]
    return " ".join(candidates[:2]) if candidates else "AI"
