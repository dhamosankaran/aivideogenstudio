"""
Shared helpers for parsing LLM responses.

Consolidates the JSON extraction logic that was duplicated across
content_analyzer.py, metadata_generation_service.py, book_service.py,
and clip_extractor_service.py.
"""

import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def parse_llm_json(response: str, *, strict: bool = False) -> Optional[dict]:
    """
    Extract and parse JSON from an LLM text response.

    Handles common LLM response quirks:
    - Markdown code fences (```json ... ```)
    - Leading/trailing prose around the JSON object
    - Whitespace variations

    Args:
        response: Raw LLM response string.
        strict: If True, raise ValueError on failure instead of returning None.

    Returns:
        Parsed dict, or None if parsing fails and strict is False.

    Raises:
        ValueError: If strict=True and JSON cannot be extracted.
    """
    if not response or not response.strip():
        if strict:
            raise ValueError("Empty LLM response")
        return None

    text = response.strip()

    # Step 1: Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines).strip()

    # Step 2: Try direct parse first (fastest path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Step 3: Extract JSON object between first { and last }
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"JSON found but invalid: {e}")

    # Step 4: Try extracting JSON array between [ and ]
    array_match = re.search(r'\[[\s\S]*\]', text)
    if array_match:
        try:
            return json.loads(array_match.group())
        except json.JSONDecodeError:
            pass

    # All attempts failed
    msg = f"Could not extract JSON from LLM response ({len(response)} chars)"
    logger.error(msg)
    logger.debug(f"Response was: {response[:500]}")

    if strict:
        raise ValueError(msg)
    return None
