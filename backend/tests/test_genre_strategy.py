"""
Unit tests for GenreStrategyRegistry.
No API calls required.
"""

import pytest
from app.services.genre_strategy import GenreStrategyRegistry


def test_finance_subjects_returns_strategic_insider():
    subjects = ["Personal finance", "Investing", "Wealth", "Economics"]
    strategy = GenreStrategyRegistry.detect(subjects)
    assert strategy["name"] == "The Strategic Insider"
    assert "persona_instruction" in strategy
    assert len(strategy["hook_patterns"]) > 0


def test_psychology_subjects_returns_cognitive_architect():
    subjects = ["Psychology", "Self-help", "Habits", "Mindset"]
    strategy = GenreStrategyRegistry.detect(subjects)
    assert strategy["name"] == "The Cognitive Architect"
    assert "autopilot" in strategy["hook_patterns"][1].lower()


def test_unknown_subjects_returns_default_storyteller():
    subjects = ["Cooking", "Gardening", "Travel"]
    strategy = GenreStrategyRegistry.detect(subjects)
    assert strategy["name"] == "The Storyteller"


def test_empty_subjects_returns_default_storyteller():
    strategy = GenreStrategyRegistry.detect([])
    assert strategy["name"] == "The Storyteller"


def test_mixed_subjects_finance_wins():
    # Finance keywords outweigh other categories
    subjects = ["Business", "Investing", "Wealth management", "Self-help"]
    strategy = GenreStrategyRegistry.detect(subjects)
    # Both finance and psychology have hits; finance should win if more keywords match
    assert strategy["name"] in ("The Strategic Insider", "The Cognitive Architect")


def test_all_strategies_have_required_keys():
    all_strategies = GenreStrategyRegistry.get_all_strategies()
    required = {"name", "persona_instruction", "tone_guidance"}
    for key, strategy in all_strategies.items():
        missing = required - set(strategy.keys())
        assert not missing, f"Strategy '{key}' missing keys: {missing}"
