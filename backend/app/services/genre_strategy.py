"""
Genre-Aware Narrative Engine for Book Reviews.

Maps book categories (from Open Library subjects) to storytelling personas.
Each persona defines hook style, tone, and visual emphasis for the script
generation prompt, upgrading the pipeline from generic "Explainer" to
a high-retention "Story-Driven" engine.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─── Genre Strategy Definitions ──────────────────────────────────

GENRE_STRATEGIES: Dict[str, dict] = {
    # ── Finance / Wealth / Business ──
    "strategic_insider": {
        "name": "The Strategic Insider",
        "match_keywords": [
            # Unambiguous finance/money signals — no overlap with self-help
            "finance", "wealth", "money", "investing", "economics",
            "entrepreneurship", "capitalism", "stock market",
            "financial", "personal finance", "wall street",
            "millionaire", "billionaire", "trading", "real estate",
            "accounting", "budgeting", "debt", "passive income",
            "venture capital", "startup", "portfolio",
        ],
        "persona_instruction": (
            "You are 'The Strategic Insider' — a narrator who reveals the hidden psychology "
            "of power and wealth that the establishment doesn't want people to know. "
            "Your tone is conspiratorial but credible, like a wise mentor sharing "
            "forbidden knowledge over a private dinner."
        ),
        "hook_patterns": [
            "This book was banned in prisons because it made inmates too financially dangerous.",
            "The rich don't want you to read this. Here's why.",
            "Most people don't want to be millionaires — they want to SPEND a million dollars. "
            "That's the fastest way to stay broke.",
            "This book reveals the one money rule that separates the wealthy from everyone else.",
        ],
        "tone_guidance": (
            "- Lead with 'Forbidden Knowledge' hooks — make the viewer feel like they're "
            "accessing insider secrets\n"
            "- Focus on the HIDDEN PSYCHOLOGY behind money decisions\n"
            "- Use power dynamics language: 'the system', 'what they don't teach you', "
            "'the real game'\n"
            "- Frame each takeaway as a strategic advantage the reader gains\n"
            "- Replace generic advice with psychological insights: instead of 'save money', "
            "say 'understand why your brain sabotages your wealth'\n"
            "- End with a provocative identity question: 'Are you investing for growth or ego?'"
        ),
        "visual_emphasis": (
            "Dark, luxurious, powerful imagery. Think: mahogany desks, dramatic rim lighting, "
            "close-ups of currency, chess pieces, boardrooms. Moody and cinematic."
        ),
    },

    # ── Self-Help / Psychology / Mindset ──
    "cognitive_architect": {
        "name": "The Cognitive Architect",
        "match_keywords": [
            # Core psychology/mind terms
            "self-help", "psychology", "mindset", "habits", "motivation",
            "self-improvement", "personal development", "productivity",
            "mental health", "emotional intelligence", "cognitive",
            "behavioral", "neuroscience", "thinking", "decision making",
            "mindfulness", "meditation", "stoicism", "philosophy",
            "happiness", "resilience", "growth mindset", "brain",
            "consciousness", "therapy", "well-being", "anxiety",
            # Also claim leadership/business/success when paired with psychology
            "leadership", "business", "success", "perseverance",
            "grit", "willpower", "self-discipline", "performance",
        ],
        "persona_instruction": (
            "You are 'The Cognitive Architect' — a narrator who makes complex psychological "
            "concepts feel intuitive by translating them into vivid, everyday metaphors. "
            "You explain the mind like an engineer explains a machine — with clarity, "
            "wonder, and precision."
        ),
        "hook_patterns": [
            "Your brain has two pilots. One is flying the plane. The other is asleep. "
            "This book teaches you which one to wake up.",
            "You're not lazy. Your autopilot is just miscalibrated. Here's the fix.",
            "What if everything you thought about willpower was completely wrong?",
            "This book rewires how 10 million people think. Here's the blueprint.",
        ],
        "tone_guidance": (
            "- Replace ALL technical jargon with relatable metaphors:\n"
            "  • 'System 1 / System 2' → 'Your Autopilot vs. Your Pilot'\n"
            "  • 'Cognitive bias' → 'mental blind spots'\n"
            "  • 'Neuroplasticity' → 'rewiring your brain'\n"
            "  • 'Habit loop' → 'the invisible program running your day'\n"
            "- Use 'think of it like...' bridges to introduce each concept\n"
            "- Frame insights as revelations about the viewer's OWN mind\n"
            "- Make abstract ideas PHYSICAL: 'Your willpower isn't a muscle — it's a battery'\n"
            "- End with a self-discovery question: 'Which mental blind spot has been running your life?'"
        ),
        "visual_emphasis": (
            "Brain metaphors made visual. Think: split-screen contrasts (chaos vs. clarity), "
            "light bulb moments, paths diverging, mirrors, soft golden lighting. "
            "Clean, thoughtful, and human-centric."
        ),
    },

    # ── Philosophy / Stoicism / Existentialism ──
    "philosophical_sage": {
        "name": "The Philosophical Sage",
        "match_keywords": [
            # Core philosophy signals
            "philosophy", "stoicism", "existentialism", "ethics",
            "metaphysics", "epistemology", "ontology", "logic",
            "moral philosophy", "political philosophy", "aesthetics",
            # Specific traditions & thinkers
            "ancient philosophy", "eastern philosophy", "western philosophy",
            "buddhism", "taoism", "zen", "confucianism",
            "nietzsche", "plato", "aristotle", "seneca", "marcus aurelius",
            "epictetus", "camus", "sartre", "kierkegaard", "schopenhauer",
            # Thematic concepts
            "meaning of life", "free will", "consciousness", "virtue",
            "wisdom", "mortality", "suffering", "impermanence",
            "purpose", "contemplation", "inner peace", "the good life",
            "absurdism", "nihilism", "pragmatism", "rationalism",
        ],
        "persona_instruction": (
            "You are 'The Philosophical Sage' — a calm, deeply reflective narrator who "
            "distills millennia of human thought into quiet, powerful insights. Your tone "
            "is unhurried and contemplative, like a wise friend sharing timeless truths "
            "over morning coffee as the sun rises. You make ancient wisdom feel urgently "
            "relevant to modern life."
        ),
        "hook_patterns": [
            "Two thousand years ago, a Roman emperor wrote a private journal that was "
            "never meant to be read. It now outsells every self-help book on Earth.",
            "You are going to die. That's not a threat — it's the most liberating "
            "idea in this entire book.",
            "What if the key to happiness isn't getting more — but wanting less? "
            "This ancient philosophy proves it.",
            "This book doesn't teach you how to succeed. It teaches you how to be free.",
        ],
        "tone_guidance": (
            "- Open with a PARADOX or a timeless question that stops the viewer\n"
            "- Use the cadence of a quiet revelation, not a loud proclamation\n"
            "- Bridge ancient ideas to modern struggles: 'Seneca said this 2,000 years ago — "
            "your phone proves him right every day'\n"
            "- Replace self-help jargon with philosophical clarity: instead of 'optimize your morning', "
            "say 'choose how you meet the day'\n"
            "- Frame each takeaway as a CHOICE, not a hack: 'You can react, or you can respond. "
            "This book teaches you the difference.'\n"
            "- End with a question about how the viewer wants to LIVE, not what they want to achieve: "
            "'Are you living your life — or just running through it?'"
        ),
        "visual_emphasis": (
            "Peace, choice, and quiet grandeur. Think: a silhouette on a balcony at sunrise, "
            "soft morning light, a person holding coffee overlooking a quiet city, ancient stone "
            "architecture, open journals with handwritten notes, candlelit rooms, vast landscapes "
            "with a single figure. Shallow depth of field, warm and contemplative."
        ),
    },
}

# ── Default strategy (current behavior, unchanged) ──
DEFAULT_STRATEGY: dict = {
    "name": "The Storyteller",
    "persona_instruction": (
        "You are a professional book reviewer creating an engaging YouTube Shorts script. "
        "Your book review videos get thousands of views because they are well-structured, "
        "informative, and visually compelling."
    ),
    "hook_patterns": [],
    "tone_guidance": (
        "- Speak like a knowledgeable friend recommending a life-changing book\n"
        "- Clear, articulate sentences (8-12 words each)\n"
        "- Be enthusiastic but authentic — NOT salesy or hype-driven\n"
        "- Every sentence MUST add value — zero filler"
    ),
    "visual_emphasis": "",
}


class GenreStrategyRegistry:
    """Registry that detects book genre and returns the matching storytelling strategy."""

    @staticmethod
    def detect(subjects: List[str]) -> dict:
        """
        Detect the best genre strategy based on book subjects.

        Scoring rules:
        - Strategic Insider: each matched finance keyword = 1 point
        - Cognitive Architect: core psychology keywords = 2 points each,
          shared/generic keywords (leadership, business, success) = 1 point each
          → requires minimum score of 2 to avoid single-word mismatches
        - Philosophical Sage: core philosophy keywords = 2 points each,
          shared keywords (consciousness, wisdom, purpose) = 1 point each
          → requires minimum score of 2

        Args:
            subjects: List of subject strings from Open Library

        Returns:
            Strategy dict with persona_instruction, hook_patterns, tone_guidance, visual_emphasis
        """
        if not subjects:
            logger.info("[GenreStrategy] No subjects provided, using default Storyteller persona")
            return DEFAULT_STRATEGY

        # Normalize subjects to lowercase for matching
        normalized = [s.lower().strip() for s in subjects]
        subjects_text = " ".join(normalized)

        scores: dict = {}

        # ── Strategic Insider: all keywords score equally ──
        si = GENRE_STRATEGIES["strategic_insider"]
        scores["strategic_insider"] = sum(
            1 for kw in si["match_keywords"] if kw in subjects_text
        )

        # ── Cognitive Architect: strong psychology keywords score 2x,
        #    generic shared keywords (business, leadership, success…) score 1x ──
        ca = GENRE_STRATEGIES["cognitive_architect"]
        STRONG_CA_KEYWORDS = {
            "self-help", "psychology", "mindset", "habits", "motivation",
            "self-improvement", "personal development", "productivity",
            "mental health", "emotional intelligence", "cognitive",
            "behavioral", "neuroscience", "thinking", "decision making",
            "mindfulness", "meditation", "stoicism", "philosophy",
            "happiness", "resilience", "growth mindset", "brain",
            "consciousness", "therapy", "well-being", "anxiety",
        }
        ca_score = 0
        for kw in ca["match_keywords"]:
            if kw in subjects_text:
                ca_score += 2 if kw in STRONG_CA_KEYWORDS else 1
        scores["cognitive_architect"] = ca_score

        # ── Philosophical Sage: strong philosophy keywords score 2x,
        #    shared keywords (consciousness, wisdom, purpose) score 1x ──
        ps = GENRE_STRATEGIES["philosophical_sage"]
        STRONG_PS_KEYWORDS = {
            "philosophy", "stoicism", "existentialism", "ethics",
            "metaphysics", "epistemology", "ontology", "logic",
            "moral philosophy", "political philosophy", "aesthetics",
            "ancient philosophy", "eastern philosophy", "western philosophy",
            "buddhism", "taoism", "zen", "confucianism",
            "nietzsche", "plato", "aristotle", "seneca", "marcus aurelius",
            "epictetus", "camus", "sartre", "kierkegaard", "schopenhauer",
            "meaning of life", "free will", "virtue", "mortality",
            "suffering", "impermanence", "contemplation", "inner peace",
            "the good life", "absurdism", "nihilism", "pragmatism", "rationalism",
        }
        ps_score = 0
        for kw in ps["match_keywords"]:
            if kw in subjects_text:
                ps_score += 2 if kw in STRONG_PS_KEYWORDS else 1
        scores["philosophical_sage"] = ps_score

        # Find best match
        best_key = max(scores, key=lambda k: scores[k])
        best_score = scores[best_key]

        # Minimum thresholds: SI needs 1+, CA needs 2+, PS needs 2+
        # (prevents a single generic keyword like 'philosophy' triggering PS over CA)
        MIN_SCORES = {"strategic_insider": 1, "cognitive_architect": 2, "philosophical_sage": 2}

        if best_score >= MIN_SCORES.get(best_key, 1):
            strategy = GENRE_STRATEGIES[best_key]
            logger.info(
                f"[GenreStrategy] Detected '{strategy['name']}' persona "
                f"(score={best_score}, matched from {len(normalized)} subjects)"
            )
            return strategy

        logger.info("[GenreStrategy] No strong genre match, using default Storyteller persona")
        return DEFAULT_STRATEGY


    @staticmethod
    def get_all_strategies() -> Dict[str, dict]:
        """Return all registered strategies including default."""
        return {
            **GENRE_STRATEGIES,
            "default": DEFAULT_STRATEGY,
        }
