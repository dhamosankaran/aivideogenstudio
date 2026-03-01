"""
Caption Service for Phase 4.

Generates SRT/ASS captions from transcript timestamps or LLM summaries.
Supports phrase-level grouping for a polished subtitle look.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CaptionService:
    """Generate and apply captions to videos."""

    def __init__(self):
        pass

    # ── From transcript ─────────────────────────────────────────

    def generate_captions_from_transcript(
        self,
        transcript_segments: List[Dict[str, Any]],
        style: str = "phrase",
        words_per_phrase: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate caption entries from transcript segments.

        Args:
            transcript_segments: List of {text, start, end}
            style: "word" for word-by-word, "phrase" for grouped phrases
            words_per_phrase: Number of words per phrase (for phrase style)

        Returns:
            List of caption dicts: [{text, start, end}, ...]
        """
        if style == "word":
            return self._word_level_captions(transcript_segments)
        else:
            return self._phrase_level_captions(transcript_segments, words_per_phrase)

    def _word_level_captions(
        self, segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Split transcript segments into individual word captions."""
        captions = []
        for seg in segments:
            text = seg.get("text", "").strip()
            start = seg.get("start", 0)
            end = seg.get("end", start + 2)
            if not text:
                continue

            words = text.split()
            if not words:
                continue

            word_duration = (end - start) / len(words)
            for i, word in enumerate(words):
                w_start = start + i * word_duration
                w_end = w_start + word_duration
                captions.append({
                    "text": word,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                })
        return captions

    def _phrase_level_captions(
        self, segments: List[Dict[str, Any]], words_per_phrase: int = 5
    ) -> List[Dict[str, Any]]:
        """Group transcript segments into multi-word phrase captions."""
        # First, flatten all words with timestamps
        all_words = []
        for seg in segments:
            text = seg.get("text", "").strip()
            start = seg.get("start", 0)
            end = seg.get("end", start + 2)
            if not text:
                continue

            words = text.split()
            if not words:
                continue

            word_duration = (end - start) / len(words)
            for i, word in enumerate(words):
                w_start = start + i * word_duration
                w_end = w_start + word_duration
                all_words.append({
                    "text": word,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                })

        # Group into phrases
        captions = []
        for i in range(0, len(all_words), words_per_phrase):
            chunk = all_words[i : i + words_per_phrase]
            if not chunk:
                continue
            phrase_text = " ".join(w["text"] for w in chunk)
            phrase_start = chunk[0]["start"]
            phrase_end = chunk[-1]["end"]
            captions.append({
                "text": phrase_text,
                "start": phrase_start,
                "end": phrase_end,
            })

        return captions

    # ── From LLM ────────────────────────────────────────────────

    async def generate_captions_from_llm(
        self,
        summary_text: str,
        duration: float,
        num_captions: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Generate timed captions using LLM when no transcript is available.

        Args:
            summary_text: Text summary of the video content
            duration: Total video duration in seconds
            num_captions: Number of caption entries to generate

        Returns:
            List of caption dicts: [{text, start, end}, ...]
        """
        # Split summary into roughly equal segments
        sentences = [s.strip() for s in summary_text.replace("\n", " ").split(".") if s.strip()]
        if not sentences:
            return []

        captions = []
        segment_duration = duration / len(sentences)

        for i, sentence in enumerate(sentences):
            start = i * segment_duration
            end = start + segment_duration
            # Trim very long sentences
            text = sentence[:80] + "..." if len(sentence) > 80 else sentence
            if not text.endswith("."):
                text += "."
            captions.append({
                "text": text,
                "start": round(start, 3),
                "end": round(end, 3),
            })

        return captions

    # ── SRT generation ──────────────────────────────────────────

    def captions_to_srt(
        self, captions: List[Dict[str, Any]]
    ) -> str:
        """
        Convert caption list to SRT format string.

        Args:
            captions: List of {text, start, end}

        Returns:
            SRT-formatted string
        """
        lines = []
        for i, cap in enumerate(captions, 1):
            start = self._seconds_to_srt_time(cap["start"])
            end = self._seconds_to_srt_time(cap["end"])
            lines.append(f"{i}")
            lines.append(f"{start} --> {end}")
            lines.append(cap["text"])
            lines.append("")
        return "\n".join(lines)

    def save_srt(
        self,
        captions: List[Dict[str, Any]],
        output_path: Path,
    ) -> Path:
        """Save captions as an SRT file."""
        output_path = Path(output_path)
        srt_content = self.captions_to_srt(captions)
        output_path.write_text(srt_content, encoding="utf-8")
        logger.info(f"Saved SRT: {output_path} ({len(captions)} entries)")
        return output_path

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
