"""
Prompt templates for LLM-based content generation.
"""

def build_script_generation_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    style: str = "engaging",
    target_duration: int = 90,
    scene_based: bool = True
) -> str:
    """
    Build prompt for script generation.
    
    Args:
        article_title: Title of the article
        article_summary: Summary of the article
        key_points: List of key points from analysis
        style: Script style (engaging, casual, formal)
        target_duration: Target duration in seconds
        scene_based: Whether to generate scene-based structure
        
    Returns:
        Formatted prompt string
    """
    
    if scene_based:
        return _build_scene_based_prompt(
            article_title, article_summary, key_points, style, target_duration
        )
    else:
        return _build_simple_prompt(
            article_title, article_summary, key_points, style, target_duration
        )


def _build_scene_based_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    style: str,
    target_duration: int
) -> str:
    """Build scene-based script generation prompt (NotebookLM style)."""
    
    key_points_text = "\n".join(f"- {point}" for point in key_points)
    
    return f"""You are a professional YouTube Shorts scriptwriter specializing in AI and technology content.

Create an engaging {target_duration}-second video script about:
**Title**: {article_title}

**Summary**: {article_summary}

**Key Points**:
{key_points_text}

**Requirements**:
1. Structure the script into 3-4 distinct scenes (10-15 seconds each)
2. Each scene should have:
   - Engaging narration that flows naturally
   - 2-3 image search keywords (for finding relevant stock photos)
   - A visual style hint (tech_modern, corporate, nature, abstract, futuristic)
3. Use a {style} tone throughout
4. Start with a hook that grabs attention in the first 3 seconds
5. End with a strong call-to-action or thought-provoking statement
6. Write for spoken delivery (conversational, not formal)
7. Total word count: 180-250 words (for {target_duration}s at 2.5 words/second)

**Output Format** (JSON):
{{
  "hook": "Opening line that grabs attention",
  "scenes": [
    {{
      "scene_number": 1,
      "text": "Narration for this scene...",
      "image_keywords": ["keyword1", "keyword2", "keyword3"],
      "visual_style": "tech_modern",
      "duration_estimate": 15
    }},
    {{
      "scene_number": 2,
      "text": "Narration for next scene...",
      "image_keywords": ["keyword1", "keyword2"],
      "visual_style": "corporate",
      "duration_estimate": 20
    }}
  ],
  "call_to_action": "Final thought or CTA"
}}

**Style Guidelines for "{style}"**:
- engaging: Energetic, uses "you", asks questions, creates urgency
- casual: Conversational, uses contractions, friendly tone
- formal: Professional, authoritative, fact-focused

Generate the script now in valid JSON format:"""


def _build_simple_prompt(
    article_title: str,
    article_summary: str,
    key_points: list,
    style: str,
    target_duration: int
) -> str:
    """Build simple (legacy) script generation prompt."""
    
    key_points_text = "\n".join(f"- {point}" for point in key_points)
    
    return f"""You are a professional YouTube Shorts scriptwriter specializing in AI and technology content.

Create an engaging {target_duration}-second video script about:
**Title**: {article_title}

**Summary**: {article_summary}

**Key Points**:
{key_points_text}

**Requirements**:
1. Hook viewers in the first 3 seconds
2. Use a {style} tone
3. Target word count: 250-350 words (for {target_duration}s)
4. Write for spoken delivery
5. End with a call-to-action

Generate the script now:"""


def build_article_analysis_prompt(
    title: str,
    description: str,
    content_preview: str,
    published_at: str,
    source: str
) -> str:
    """
    Build prompt for article analysis and scoring.
    
    Args:
        title: Article title
        description: Article description
        content_preview: Preview of article content
        published_at: Publication date
        source: Source name
        
    Returns:
        Formatted prompt string
    """
    return f"""You are an AI content analyst specializing in technology and AI news.

Analyze this article and provide scores and insights:

**Article Details**:
- Title: {title}
- Source: {source}
- Published: {published_at}
- Description: {description}
- Content Preview: {content_preview}

**Task**: Score this article on the following dimensions (0-10 scale):

1. **Relevance Score**: How relevant is this to AI/tech audience?
2. **Engagement Score**: How likely to engage viewers (viral potential)?
3. **Recency Score**: How timely/newsworthy is this?
4. **Uniqueness Score**: How unique/novel is this content?

Also provide:
- **Category**: Main category (e.g., "AI Research", "Tech News", "Product Launch")
- **Key Topics**: List of 3-5 key topics/keywords
- **Why Interesting**: Brief explanation of why this is interesting (1-2 sentences)

**Output Format** (JSON):
{{
  "relevance_score": 8.5,
  "engagement_score": 7.0,
  "recency_score": 9.0,
  "uniqueness_score": 6.5,
  "category": "AI Research",
  "key_topics": ["GPT-4", "language models", "AI safety"],
  "why_interesting": "Groundbreaking research that could change how we interact with AI."
}}

Provide your analysis in valid JSON format:"""
