"""
Pattern Interrupt Service for 7-Second Retention Logic.

Injects visual and audio resets every 7-10 seconds during video composition
to maintain viewer attention. Based on the mechanical retention principle
that viewers' attention naturally wanes after 7-10 seconds of static content.

Visual interrupts: Alternating Ken Burns directions (push-in / pull-out)
Audio interrupts: Subtle whoosh/thud SFX at transition points
"""

import math
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ── SFX asset paths ──
SFX_DIR = Path("backend/assets/sfx")


class PatternInterruptService:
    """Service that plans and provides retention-boosting interrupts."""

    # Interrupt interval range (seconds)
    MIN_INTERVAL = 7
    MAX_INTERVAL = 10

    def __init__(self):
        """Initialize and ensure SFX assets exist."""
        SFX_DIR.mkdir(parents=True, exist_ok=True)

    def plan_interrupts(
        self,
        scenes: List[Dict],
        total_duration: float
    ) -> List[Dict]:
        """
        Plan pattern interrupts across the video timeline.

        Returns a list of interrupt events, each with:
        - time: seconds offset into the video
        - type: "visual" or "audio"
        - visual_action: "push_in" or "pull_out" (for Ken Burns direction)
        - sfx_type: "whoosh" or "thud" (for audio interrupts)

        Args:
            scenes: List of scene dicts with "start_time" and "duration" keys
            total_duration: Total video duration in seconds

        Returns:
            List of interrupt event dicts
        """
        interrupts = []
        current_time = 0.0
        direction_toggle = True  # True = push_in, False = pull_out

        while current_time < total_duration:
            # Alternate interval between MIN and MAX for organic feel
            interval = self.MIN_INTERVAL if direction_toggle else self.MAX_INTERVAL
            current_time += interval

            if current_time >= total_duration - 1.0:
                break

            # Determine interrupt type: visual at scene boundaries, audio otherwise
            is_scene_boundary = any(
                abs(scene.get("start_time", -999) - current_time) < 1.5
                for scene in scenes
            )

            if is_scene_boundary:
                interrupt_type = "visual"
            else:
                interrupt_type = "audio"

            interrupts.append({
                "time": round(current_time, 2),
                "type": interrupt_type,
                "visual_action": "push_in" if direction_toggle else "pull_out",
                "sfx_type": "whoosh" if direction_toggle else "thud",
            })

            direction_toggle = not direction_toggle

        logger.info(
            f"[PatternInterrupt] Planned {len(interrupts)} interrupts "
            f"across {total_duration:.1f}s video"
        )
        return interrupts

    def get_scene_directions(self, num_scenes: int) -> List[str]:
        """
        Get alternating Ken Burns directions for each scene.

        Args:
            num_scenes: Total number of scenes

        Returns:
            List of "push_in" or "pull_out" strings, one per scene
        """
        return [
            "push_in" if i % 2 == 0 else "pull_out"
            for i in range(num_scenes)
        ]

    def get_sfx_clip(self, sfx_type: str = "whoosh", duration: float = 0.3):
        """
        Get an audio clip for a transition sound effect.

        Generates clips programmatically using numpy if asset files
        don't exist, ensuring zero external dependencies.

        Args:
            sfx_type: "whoosh" or "thud"
            duration: Duration of the SFX in seconds

        Returns:
            MoviePy AudioClip, or None if generation fails
        """
        try:
            from moviepy import AudioClip

            sample_rate = 44100

            if sfx_type == "whoosh":
                return self._generate_whoosh(duration, sample_rate)
            else:
                return self._generate_thud(duration, sample_rate)

        except Exception as e:
            logger.warning(f"[PatternInterrupt] SFX generation failed: {e}")
            return None

    def _generate_whoosh(self, duration: float, sample_rate: int):
        """Generate a subtle whoosh sound (rising frequency sweep)."""
        from moviepy import AudioClip

        def make_frame(t):
            t_arr = np.atleast_1d(np.asarray(t, dtype=float))
            # Rising frequency sweep from 200Hz to 2000Hz with fade envelope
            freq = 200 + 1800 * (t_arr / duration)
            # Envelope: quick attack, slow decay
            envelope = np.sin(np.pi * t_arr / duration) ** 0.5
            # White noise component for "air" texture
            noise = np.random.normal(0, 0.05, t_arr.shape)
            # Sine sweep + noise
            signal = 0.15 * envelope * (
                np.sin(2 * np.pi * freq * t_arr) * 0.4 + noise * 0.6
            )
            # Stereo (two channels)
            return np.column_stack([signal, signal])

        clip = AudioClip(make_frame, duration=duration, fps=sample_rate)
        return clip

    def _generate_thud(self, duration: float, sample_rate: int):
        """Generate a subtle low-frequency thud (bass impact)."""
        from moviepy import AudioClip

        def make_frame(t):
            t_arr = np.atleast_1d(np.asarray(t, dtype=float))
            # Low frequency impact: 60Hz with exponential decay
            freq = 60
            decay = np.exp(-8 * t_arr / duration)
            signal = 0.2 * decay * np.sin(2 * np.pi * freq * t_arr)
            # Stereo
            return np.column_stack([signal, signal])

        clip = AudioClip(make_frame, duration=duration, fps=sample_rate)
        return clip

