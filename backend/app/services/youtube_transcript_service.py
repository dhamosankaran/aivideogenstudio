"""
YouTube Transcript Service for Phase 2.5.

Handles:
- Extracting transcripts from YouTube videos
- Analyzing transcripts for key insights using LLM
- Creating articles from insights for the existing pipeline
"""

import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

from app.models import YouTubeSource, Article
from app.services.provider_factory import ProviderFactory, LLMProvider
from app.services.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class KeyInsight:
    """Represents a key insight extracted from a YouTube video transcript."""
    
    def __init__(
        self,
        start_time: float,
        end_time: float,
        transcript_text: str,
        summary: str,
        hook: str,
        key_points: List[str],
        viral_score: int,
        engagement_type: str
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.transcript_text = transcript_text
        self.summary = summary
        self.hook = hook
        self.key_points = key_points
        self.viral_score = viral_score
        self.engagement_type = engagement_type
        self.formatted_time = self._format_timestamp(start_time)
        self.formatted_end_time = self._format_timestamp(end_time)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "transcript_text": self.transcript_text,
            "summary": self.summary,
            "hook": self.hook,
            "key_points": self.key_points,
            "viral_score": self.viral_score,
            "engagement_type": self.engagement_type,
            "formatted_time": self.formatted_time,
            "formatted_end_time": self.formatted_end_time
        }


class YouTubeTranscriptService:
    """Service for YouTube transcript extraction and insight analysis."""
    
    def __init__(
        self,
        db: Session,
        llm_provider: Optional[BaseLLMProvider] = None
    ):
        """
        Initialize the service.
        
        Args:
            db: Database session
            llm_provider: Optional LLM provider (defaults to Gemini)
        """
        self.db = db
        self.llm = llm_provider or ProviderFactory.create_llm_provider(
            provider=LLMProvider.GEMINI
        )
    
    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from various YouTube URL formats.
        
        Supports:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/v/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID
        """
        patterns = [
            r'(?:v=|\/v\/|youtu\.be\/|embed\/|\/watch\?v=|\/shorts\/)([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        
        return None
    
    async def extract_transcript(self, youtube_url: str) -> YouTubeSource:
        """
        Extract transcript from a YouTube video and store it.
        
        Args:
            youtube_url: Full YouTube URL
            
        Returns:
            YouTubeSource with transcript data
            
        Raises:
            ValueError: If URL is invalid or transcript unavailable
        """
        video_id = self.extract_video_id(youtube_url)
        if not video_id:
            raise ValueError(f"Invalid YouTube URL: {youtube_url}")
        
        # Check if already exists
        existing = self.db.query(YouTubeSource).filter(
            YouTubeSource.youtube_video_id == video_id
        ).first()
        
        if existing:
            logger.info(f"YouTube source already exists: {video_id}")
            return existing
        
        logger.info(f"Extracting transcript for video: {video_id}")
        
        try:
            # Get transcript with timestamps (youtube-transcript-api v1.2.4+)
            api = YouTubeTranscriptApi()
            result = api.fetch(video_id)
            
            # Convert to list of dicts (old format) for compatibility
            transcript_list = [
                {'text': s.text, 'start': s.start, 'duration': s.duration} 
                for s in result.snippets
            ]
            
            # Calculate total duration
            if transcript_list:
                last_segment = transcript_list[-1]
                total_duration = last_segment['start'] + last_segment.get('duration', 0)
            else:
                total_duration = 0
            
            # Create YouTubeSource record
            youtube_source = YouTubeSource(
                youtube_url=youtube_url,
                youtube_video_id=video_id,
                transcript=transcript_list,
                duration_seconds=total_duration,
                analysis_status="pending",
                thumbnail_url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            )
            
            self.db.add(youtube_source)
            self.db.commit()
            self.db.refresh(youtube_source)
            
            logger.info(f"Transcript extracted: {len(transcript_list)} segments, {total_duration:.1f}s total")
            return youtube_source
            
        except TranscriptsDisabled:
            raise ValueError(f"Transcripts are disabled for video: {video_id}")
        except NoTranscriptFound:
            raise ValueError(f"No transcript found for video: {video_id}")
        except Exception as e:
            logger.error(f"Failed to extract transcript: {str(e)}")
            raise ValueError(f"Failed to extract transcript: {str(e)}")
    
    async def analyze_for_insights(self, youtube_source_id: int) -> List[KeyInsight]:
        """
        Analyze a transcript to find key insights for Shorts creation.
        
        Args:
            youtube_source_id: ID of the YouTubeSource to analyze
            
        Returns:
            List of KeyInsight objects
        """
        source = self.db.query(YouTubeSource).filter(
            YouTubeSource.id == youtube_source_id
        ).first()
        
        if not source:
            raise ValueError(f"YouTubeSource not found: {youtube_source_id}")
        
        if not source.transcript:
            raise ValueError("No transcript available for analysis")
        
        # Update status
        source.analysis_status = "analyzing"
        self.db.commit()
        
        try:
            # Build full transcript text with timestamps
            transcript_text = self._build_transcript_text(source.transcript)
            
            # Build LLM prompt
            prompt = self._build_insight_extraction_prompt(
                transcript_text=transcript_text,
                video_title=source.title or "Unknown Video",
                duration_seconds=source.duration_seconds or 0
            )
            
            # Call LLM
            from app.schemas.youtube_schemas import InsightsOutput
            
            response = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_tokens=4000,
                response_mime_type="application/json",
                response_schema=InsightsOutput
            )
            
            # Parse response
            insights_data = InsightsOutput.model_validate_json(response)
            
            # Convert to KeyInsight objects with null safety
            insights = []
            for item in insights_data.insights:
                # Calculate end_time if missing (default: start + 30 seconds)
                end_time = item.end_time if item.end_time else item.start_time + 30.0
                
                insight = KeyInsight(
                    start_time=item.start_time,
                    end_time=end_time,
                    transcript_text=item.transcript_text or "",
                    summary=item.summary or "Key insight from video",
                    hook=item.hook or "Check this out!",
                    key_points=item.key_points or [],
                    viral_score=item.viral_score or 5,
                    engagement_type=item.engagement_type or "practical"
                )
                insights.append(insight)
            
            # Sort by viral score (highest first)
            insights.sort(key=lambda x: x.viral_score, reverse=True)
            
            # Store insights in database
            source.insights = [i.to_dict() for i in insights]
            source.analysis_status = "completed"
            source.analyzed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Analysis complete: {len(insights)} insights found for source {youtube_source_id}")
            return insights
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            source.analysis_status = "failed"
            source.error_message = str(e)
            self.db.commit()
            raise
    
    async def generate_video_summary(self, youtube_source_id: int) -> str:
        """
        Generate a comprehensive summary of the entire YouTube video.
        
        Args:
            youtube_source_id: ID of the YouTubeSource to summarize
            
        Returns:
            The generated summary text
        """
        source = self.db.query(YouTubeSource).filter(
            YouTubeSource.id == youtube_source_id
        ).first()
        
        if not source:
            raise ValueError(f"YouTubeSource not found: {youtube_source_id}")
        
        # Return cached summary if exists
        if source.video_summary:
            logger.info(f"Returning cached summary for source {youtube_source_id}")
            return source.video_summary
        
        if not source.transcript:
            raise ValueError("No transcript available for summary generation")
        
        logger.info(f"Generating video summary for source {youtube_source_id}")
        
        try:
            # Build full transcript text
            transcript_text = self._build_transcript_text(source.transcript)
            
            # Truncate if too long (keep first 8000 chars for context)
            if len(transcript_text) > 8000:
                transcript_text = transcript_text[:8000] + "\n...[transcript truncated]"
            
            # Build summary prompt
            prompt = self._build_summary_prompt(
                transcript_text=transcript_text,
                video_title=source.title or "YouTube Video",
                channel_name=source.channel_name or "Unknown Channel",
                duration_seconds=source.duration_seconds or 0
            )
            
            # Generate summary
            summary = await self.llm.generate_text(
                prompt=prompt,
                temperature=0.5,
                max_tokens=1000
            )
            
            # Store in database
            source.video_summary = summary
            source.summary_generated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Video summary generated for source {youtube_source_id}: {len(summary)} chars")
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            raise
    
    def _build_summary_prompt(
        self,
        transcript_text: str,
        video_title: str,
        channel_name: str,
        duration_seconds: float
    ) -> str:
        """Build the LLM prompt for video summary generation."""
        return f'''Create a comprehensive summary of this YouTube video.

VIDEO TITLE: {video_title}
CHANNEL: {channel_name}
DURATION: {duration_seconds / 60:.1f} minutes

TRANSCRIPT:
{transcript_text}

---

Please provide a well-structured summary with:

1. **Overview** (2-3 sentences): What is this video about? Who is the speaker/creator?

2. **Key Takeaways** (3-5 bullet points): The most important insights, facts, or lessons from the video.

3. **Notable Quotes** (1-2): Any memorable or quotable statements.

4. **Content Style**: Is this educational, entertainment, opinion, news, tutorial, etc.?

5. **Target Audience**: Who would benefit most from watching this video?

Keep the summary concise but informative (under 500 words). Use markdown formatting.'''


    
    def _build_transcript_text(self, transcript: List[Dict]) -> str:
        """Build formatted transcript text with timestamps."""
        lines = []
        for segment in transcript:
            time = self._format_timestamp(segment['start'])
            text = segment['text']
            lines.append(f"[{time}] {text}")
        return "\n".join(lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _build_insight_extraction_prompt(
        self,
        transcript_text: str,
        video_title: str,
        duration_seconds: float
    ) -> str:
        """Build the LLM prompt for insight extraction."""
        return f'''Analyze this YouTube video transcript and identify the most engaging segments that would make great YouTube Shorts (15-60 seconds each).

VIDEO TITLE: {video_title}
TOTAL DURATION: {duration_seconds:.0f} seconds ({duration_seconds / 60:.1f} minutes)

TRANSCRIPT (with timestamps in [MM:SS] format):
{transcript_text}

---

YOUR TASK:
Find 3-5 key moments that would make viral YouTube Shorts. For each moment:

**CRITICAL TIMESTAMP INSTRUCTIONS:**
- Each line in the transcript starts with [MM:SS] which indicates the START TIME
- Convert MM:SS to total seconds: for example [01:23] = 83 seconds, [00:45] = 45 seconds
- start_time and end_time MUST be actual timestamps from the transcript (between 0 and {duration_seconds:.0f})
- Each segment should be 15-60 seconds long

1. **Identify engaging segments** - Look for:
   - Surprising facts or statistics
   - Controversial or thought-provoking statements
   - "Aha!" moments or insights
   - Quotable one-liners
   - Practical tips or actionable advice

2. **Rate viral potential** (1-10) based on:
   - Emotional impact (curiosity, surprise, controversy)
   - Shareability and educational value

3. **Suggest a viral hook** - First 3 seconds that grab attention

Return your analysis as JSON with this exact structure:
{{
  "insights": [
    {{
      "start_time": <START TIME IN SECONDS - must be from the [MM:SS] timestamps>,
      "end_time": <END TIME IN SECONDS - start_time + 15 to 60 seconds>,
      "transcript_text": "<exact text from this segment>",
      "summary": "<1-2 sentence summary of the insight>",
      "hook": "<suggested 3-second hook for Shorts>",
      "key_points": ["<point 1>", "<point 2>"],
      "viral_score": <1-10>,
      "engagement_type": "<educational|controversial|emotional|surprising|practical>"
    }}
  ]
}}

Focus on QUALITY over quantity. Only include truly compelling moments.'''

    async def create_article_from_insight(
        self,
        youtube_source_id: int,
        insight_index: int,
        mode: str = "B"
    ) -> Article:
        """
        Create an Article from a selected insight to feed into existing pipeline.
        
        Args:
            youtube_source_id: ID of YouTubeSource
            insight_index: Index of the insight to use
            mode: "A" for clip+commentary, "B" for original content
            
        Returns:
            Created Article
        """
        from app.models import Feed
        
        source = self.db.query(YouTubeSource).filter(
            YouTubeSource.id == youtube_source_id
        ).first()
        
        if not source:
            raise ValueError(f"YouTubeSource not found: {youtube_source_id}")
        
        if not source.insights or insight_index >= len(source.insights):
            raise ValueError(f"Invalid insight index: {insight_index}")
        
        insight = source.insights[insight_index]
        
        # Get or create YouTube Imports feed
        youtube_feed = self.db.query(Feed).filter(Feed.url == 'youtube://imports').first()
        if not youtube_feed:
            youtube_feed = Feed(
                name='YouTube Imports',
                url='youtube://imports',
                category='youtube',
                is_active=True
            )
            self.db.add(youtube_feed)
            self.db.commit()
            self.db.refresh(youtube_feed)
        
        # Build article content based on mode
        if mode == "A":
            # Mode A: Clip + Commentary - article describes what to react to
            description = f"""React to this key moment from "{source.title or 'YouTube Video'}":

TIME WINDOW: {insight['formatted_time']} - {insight['formatted_end_time']}

ORIGINAL CONTENT:
{insight['transcript_text']}

YOUR COMMENTARY SHOULD:
- Add your unique perspective on this insight
- Explain why this matters
- Provide additional context or counter-points

SUGGESTED HOOK: {insight['hook']}"""
        else:
            # Mode B: Original content inspired by insight
            description = f"""Create original content inspired by this insight:

INSIGHT: {insight['summary']}

KEY POINTS:
{chr(10).join(f"• {p}" for p in insight['key_points'])}

SUGGESTED HOOK: {insight['hook']}

SOURCE: {source.title or 'YouTube Video'} (Credit in description)"""
        
        # Build unique URL including mode to prevent duplicates
        article_url = f"{source.youtube_url}&t={int(insight['start_time'])}&mode={mode}"
        
        # Check if article already exists for this insight+mode
        existing_article = self.db.query(Article).filter(
            Article.url == article_url
        ).first()
        
        if existing_article:
            logger.info(f"Returning existing article {existing_article.id} for insight (mode {mode})")
            return existing_article
        
        # Create Article with feed_id to satisfy NOT NULL constraint
        article = Article(
            feed_id=youtube_feed.id,  # Use YouTube Imports feed
            youtube_source_id=source.id,
            title=insight['summary'][:200],
            url=article_url,
            description=description,
            content=insight['transcript_text'],
            summary=insight['summary'],
            key_points=insight['key_points'],
            relevance_score=insight['viral_score'],
            engagement_score=insight['viral_score'],
            final_score=insight['viral_score'],
            is_processed=True,
            analyzed_at=datetime.utcnow()
        )
        
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        
        logger.info(f"Created article {article.id} from insight (mode {mode})")
        return article
    
    def get_source(self, source_id: int) -> Optional[YouTubeSource]:
        """Get a YouTubeSource by ID."""
        return self.db.query(YouTubeSource).filter(
            YouTubeSource.id == source_id
        ).first()
    
    def get_all_sources(self, limit: int = 50) -> List[YouTubeSource]:
        """Get all YouTubeSource records."""
        return self.db.query(YouTubeSource).order_by(
            YouTubeSource.created_at.desc()
        ).limit(limit).all()
    
    async def update_video_metadata(self, youtube_source_id: int) -> YouTubeSource:
        """
        Fetch and update video metadata using yt-dlp.
        
        This is optional but provides title, channel, etc.
        """
        import yt_dlp
        
        source = self.db.query(YouTubeSource).filter(
            YouTubeSource.id == youtube_source_id
        ).first()
        
        if not source:
            raise ValueError(f"YouTubeSource not found: {youtube_source_id}")
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source.youtube_url, download=False)
                
                source.title = info.get('title', source.title)
                source.channel_name = info.get('uploader', source.channel_name)
                source.channel_url = info.get('uploader_url', source.channel_url)
                if info.get('duration'):
                    source.duration_seconds = float(info['duration'])
                
                self.db.commit()
                self.db.refresh(source)
                
                logger.info(f"Updated metadata for source {youtube_source_id}: {source.title}")
                return source
                
        except Exception as e:
            logger.warning(f"Failed to fetch video metadata: {str(e)}")
            return source
