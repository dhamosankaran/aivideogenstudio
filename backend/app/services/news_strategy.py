"""
News-Category Narrative Engine for Viral News Scripts.

Maps news categories (from the Viral News trending tabs) to
storytelling strategies.  Each strategy defines:
  - hook_patterns   : Pattern-interrupt openers
  - persona         : Voice and tone for the script
  - tone_guidance   : Detailed tone rules
  - visual_formula  : Nano Banana image prompt formula
  - style_suffix    : Appended to ALL image prompts
  - visual_emphasis : Category-specific visual mood
  - urgency_interval: How often visual "jitters" fire (seconds)

Mirrors the GenreStrategyRegistry pattern from genre_strategy.py.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
#  Strategy Definitions  (8 categories)
# ─────────────────────────────────────────────────────────────────

NEWS_STRATEGIES: Dict[str, dict] = {

    # ── World / International ───────────────────────────────────
    "world": {
        "name": "The Global Correspondent",
        "match_keywords": [
            "world", "global", "international", "foreign", "diplomatic",
            "geopolitical", "united nations", "nato", "g7", "g20",
            "war", "conflict", "crisis", "sanctions", "summit",
            "refugee", "protest", "revolution", "coup", "ceasefire",
            "trade war", "climate", "pandemic", "humanitarian",
            "middle east", "europe", "asia", "africa", "latin america",
        ],
        "persona_instruction": (
            "You are a fearless global correspondent reporting live from the world stage. "
            "You cover breaking international stories with the urgency of a war reporter "
            "and the clarity of a seasoned diplomat. You connect distant conflicts and "
            "global events directly to the viewer's daily life."
        ),
        "hook_patterns": [
            "BREAKING from across the globe. This changes EVERYTHING.",
            "THE WORLD IS WATCHING. And you need to know why.",
            "JUST IN from the world stage. This affects every single country.",
        ],
        "tone_guidance": (
            "- Lead with the COUNTRY and CONFLICT or EVENT in the first 3 seconds\n"
            "- Name world leaders, nations, and organizations (UN, NATO, WHO)\n"
            "- Always connect global events to local impact: 'This means for YOU...'\n"
            "- Use map-style language: 'Meanwhile in Europe...', 'From the Middle East...'\n"
            "- End with: 'Which side are you on?' or 'Is the world heading to war?'"
        ),
        "visual_formula": "[Country/Region] + [Crisis/Event] + [International Setting] + [Press Corps Lighting] + [News Ticker Overlay]",
        "style_suffix": "Photojournalistic, international news broadcast aesthetic, world map backdrops, flag overlays, dramatic press lighting, 8k resolution",
        "visual_emphasis": (
            "Global/Cinematic. Think: satellite imagery of conflict zones, UN General Assembly "
            "wide shots, waving national flags, world leaders at summit tables, "
            "protest crowds filling city squares, news tickers scrolling, "
            "war-zone correspondents in flak jackets. Authoritative and urgent."
        ),
        "urgency_interval": 5,
    },

    # ── China ───────────────────────────────────────────────────────
    "china": {
        "name": "The China Desk",
        "match_keywords": [
            "china", "chinese", "beijing", "ccp", "xi jinping",
            "taiwan", "hong kong", "south china sea", "pla",
            "baidu", "alibaba", "tencent", "huawei", "tiktok", "bytedance",
            "belt and road", "trade war", "tariff", "made in china",
            "yuan", "renminbi", "bri", "sino", "shanghai", "shenzhen",
        ],
        "persona_instruction": (
            "You are a seasoned China analyst decoding Beijing's biggest moves for a global "
            "audience. You cut through the propaganda, break geopolitical shifts, trade wars, "
            "and tech rivalries with sharp clarity and high-stakes urgency."
        ),
        "hook_patterns": [
            "BEIJING JUST MOVED. And the whole world should be paying attention.",
            "CHINA ALERT. This changes the global power balance RIGHT NOW.",
            "BREAKING from Beijing. Here's what they don't want you to know.",
        ],
        "tone_guidance": (
            "- Lead with what China DID — be specific: Xi Jinping, CCP, PLA, specific province\n"
            "- Frame it as a global impact event: 'your supply chain', 'your tech', 'your job'\n"
            "- Reference the US-China rivalry for maximum engagement\n"
            "- Name companies: Huawei, TikTok, TSMC, Apple, Nvidia\n"
            "- End with: 'Is China winning?' or 'Who stops Beijing now?'"
        ),
        "visual_formula": "[China Subject] + [Power/Action] + [Beijing/Shanghai Setting] + [Dramatic Red Gold Lighting] + [Wide Establishing Shot]",
        "style_suffix": "Cinematic geopolitical, red and gold palette, Beijing skyline at night, Great Wall aerial, dramatic wide angle, 8k resolution",
        "visual_emphasis": (
            "Red/Gold/Power. Think: Tiananmen Square at dusk, PLA military parade, "
            "Shanghai Pudong skyline at night, Great Wall aerial drone shots, "
            "Huawei 5G towers, chip factories, container ships with Chinese flags, "
            "Xi Jinping summit meetings. Monumental and high-stakes."
        ),
        "urgency_interval": 5,
    },

    # ── Technology ─────────────────────────────────────────────
    "technology": {
        "name": "The Tech Insider",
        "match_keywords": [
            "technology", "tech", "ai", "artificial intelligence", "software",
            "hardware", "startup", "silicon valley", "app", "gadget",
            "machine learning", "deep learning", "chatbot", "gpt", "gemini",
            "apple", "google", "microsoft", "meta", "openai", "nvidia",
            "semiconductor", "quantum", "cybersecurity",
        ],
        "persona_instruction": (
            "You are a rapid-fire tech insider breaking the biggest story in "
            "Silicon Valley right now. You speak with authority, drop specific "
            "numbers, and make complex tech feel urgent and personal."
        ),
        "hook_patterns": [
            "STOP SCROLLING. This changes everything about AI.",
            "JUST IN. The tech world will never be the same.",
            "THEY FINALLY DID IT. And it affects every single one of you.",
        ],
        "tone_guidance": (
            "- Lead with the biggest TECHNICAL fact first\n"
            "- Name-drop companies, models, and versions (GPT-5, Gemini 2, etc.)\n"
            "- Use 'Pattern Interrupt' words: URGENT, JUST IN, BREAKING\n"
            "- Translate tech jargon into personal impact within 5 seconds\n"
            "- End with a 'pick your side' question for comments"
        ),
        "visual_formula": "[Tech Subject] + [Action/Demo] + [Modern Lab/Office Setting] + [Neon Blue Lighting] + [Sharp Focus]",
        "style_suffix": "Cinematic close-up, neon blue lighting, digital overlays, sharp focus, 8k resolution, cyberpunk aesthetic",
        "visual_emphasis": (
            "Blue/Cyber/Glow. Think: glowing server racks, holographic interfaces, "
            "robotic arms in motion, code streams reflected in eyes, dark rooms with "
            "neon accents. Sharp, futuristic, premium."
        ),
        "urgency_interval": 5,
    },

    # ── Business ───────────────────────────────────────────────
    "business": {
        "name": "The Market Strategist",
        "match_keywords": [
            "business", "economy", "market", "stock", "finance",
            "wall street", "nasdaq", "ipo", "merger", "acquisition",
            "revenue", "profit", "ceo", "corporate", "enterprise",
            "valuation", "investment", "venture capital", "banking",
        ],
        "persona_instruction": (
            "You are a sharp Wall Street analyst breaking market-moving news. "
            "You think in numbers, speak in billions, and always tell the viewer "
            "exactly how this hits their wallet."
        ),
        "hook_patterns": [
            "URGENT. Your money is about to be affected.",
            "JUST IN. The markets are reacting RIGHT NOW.",
            "BREAKING. This deal changes the entire industry.",
        ],
        "tone_guidance": (
            "- Lead with dollar amounts or percentage changes\n"
            "- Connect every point to the viewer's bank account or job\n"
            "- Use words like 'billion', 'crashed', 'surged', 'unprecedented'\n"
            "- Name-drop specific companies and CEOs\n"
            "- End with: 'Is your portfolio ready?' or 'What would you do?'"
        ),
        "visual_formula": "[Company/Market Subject] + [Market Movement] + [Trading Floor/Boardroom] + [Dramatic Rim Lighting] + [Motion Blur on Tickers]",
        "style_suffix": "Stock market aesthetic, red and green tickers, dramatic lighting, glass boardroom, 8k cinematic, moody finance",
        "visual_emphasis": (
            "Red/Green/Power. Think: stock tickers with rapid price changes, "
            "Wall Street skyscrapers at night, executive silhouettes in glass towers, "
            "dramatic rim lighting, currency close-ups."
        ),
        "urgency_interval": 5,
    },

    # ── Politics ───────────────────────────────────────────────
    "politics": {
        "name": "The Capitol Correspondent",
        "match_keywords": [
            "politics", "political", "government", "election", "president",
            "congress", "senate", "white house", "policy", "legislation",
            "democrat", "republican", "vote", "campaign", "diplomatic",
            "geopolitical", "summit", "sanction", "regulation",
        ],
        "persona_instruction": (
            "You are a no-nonsense political correspondent standing outside "
            "the Capitol. You cut through the spin, deliver the raw facts, "
            "and tell people exactly what this means for their lives."
        ),
        "hook_patterns": [
            "BREAKING from the Capitol. This affects EVERYONE.",
            "JUST IN. The decision that changes your future.",
            "THEY JUST VOTED. And you need to see this.",
        ],
        "tone_guidance": (
            "- Stay neutral but URGENT — report the facts, name the stakes\n"
            "- Always state WHO did WHAT and WHEN in the first 5 seconds\n"
            "- Connect policy to everyday life: taxes, rights, jobs\n"
            "- Avoid partisan language — let the facts create urgency\n"
            "- End with: 'What's your take?' or 'Does this go too far?'"
        ),
        "visual_formula": "[Political Figure/Building] + [Official Action] + [Government Setting] + [Documentary Lighting] + [Press Conference Angle]",
        "style_suffix": "Photojournalistic, documentary lighting, Capitol building, official press photo aesthetic, sharp focus, 8k resolution",
        "visual_emphasis": (
            "Institutional/Documentary. Think: marble corridors, press briefings, "
            "flags waving, podium speeches, protest crowds, official seals. "
            "Clean, authoritative, CNN-quality framing."
        ),
        "urgency_interval": 6,
    },

    # ── Science ────────────────────────────────────────────────
    "science": {
        "name": "The Discovery Narrator",
        "match_keywords": [
            "science", "scientific", "research", "discovery", "study",
            "nasa", "space", "physics", "biology", "chemistry",
            "climate", "environment", "gene", "crispr", "experiment",
            "peer-reviewed", "nature", "laboratory", "cosmos",
        ],
        "persona_instruction": (
            "You are a science communicator who makes the impossible feel real. "
            "You break complex discoveries into jaw-dropping 'did you know' moments "
            "that make viewers feel like they've unlocked forbidden knowledge."
        ),
        "hook_patterns": [
            "Scientists just discovered something that changes EVERYTHING.",
            "JUST IN from the lab. This is NOT science fiction.",
            "NASA confirmed it. And nobody is talking about it.",
        ],
        "tone_guidance": (
            "- Lead with the WOW fact — the one that sounds impossible\n"
            "- Use analogies to make scale tangible ('bigger than Earth', 'smaller than a grain of sand')\n"
            "- Name the institution and journal for credibility\n"
            "- Explain WHY this matters for the average person\n"
            "- End with a mind-bending 'what if' question"
        ),
        "visual_formula": "[Scientific Subject] + [Discovery Moment] + [Lab/Space Setting] + [Clinical Lighting] + [Macro/Telescope Detail]",
        "style_suffix": "Scientific visualization, macro photography, deep space imagery, clinical precision, vivid detail, 8k hyper-realistic",
        "visual_emphasis": (
            "Cosmic/Clinical. Think: nebulae close-ups, electron microscope imagery, "
            "clean white laboratories, astronauts in zero-gravity, DNA double helix "
            "glowing, tinted scientific diagrams. Awe-inspiring."
        ),
        "urgency_interval": 6,
    },

    # ── Health ─────────────────────────────────────────────────
    "health": {
        "name": "The Health Watchdog",
        "match_keywords": [
            "health", "medical", "medicine", "hospital", "doctor",
            "fda", "cdc", "vaccine", "drug", "treatment",
            "mental health", "nutrition", "fitness", "pandemic",
            "cancer", "diabetes", "clinical trial", "public health",
        ],
        "persona_instruction": (
            "You are a trusted health journalist who breaks medical news "
            "with clinical precision. You never sensationalize — instead, you "
            "make people feel informed and in control of their health."
        ),
        "hook_patterns": [
            "URGENT health alert. This could affect YOUR family.",
            "JUST IN from the FDA. Every parent needs to hear this.",
            "Doctors are saying this changes treatment FOREVER.",
        ],
        "tone_guidance": (
            "- Lead with the health IMPACT — who is affected and how\n"
            "- Cite the institution (WHO, FDA, CDC, specific hospital)\n"
            "- Use body-relatable language: 'your immune system', 'your brain'\n"
            "- NEVER use fear-mongering — be informative and empowering\n"
            "- End with: 'Talk to your doctor' or 'What's your experience?'"
        ),
        "visual_formula": "[Health Subject] + [Medical Action] + [Hospital/Lab Setting] + [Clean White Lighting] + [Shallow Depth of Field]",
        "style_suffix": "Medical photography, clean clinical lighting, shallow depth of field, hospital aesthetic, sharp detail, 8k resolution",
        "visual_emphasis": (
            "Clinical/Human. Think: stethoscopes, MRI scans, doctor-patient interactions, "
            "microscopic cells, clean hospital corridors, pill close-ups, "
            "healthcare workers in action. Trustworthy and precise."
        ),
        "urgency_interval": 6,
    },

    # ── Entertainment ──────────────────────────────────────────
    "entertainment": {
        "name": "The Pop Culture Pulse",
        "match_keywords": [
            "entertainment", "celebrity", "movie", "music", "hollywood",
            "netflix", "disney", "streaming", "concert", "award",
            "grammy", "oscar", "box office", "viral", "tiktok",
            "influencer", "drama", "scandal", "red carpet",
        ],
        "persona_instruction": (
            "You are the hottest entertainment insider with all the tea. "
            "You speak with energy, excitement, and the kind of urgency that "
            "makes people screenshot your videos and tag their friends."
        ),
        "hook_patterns": [
            "OH MY GOD. You will NOT believe what just happened.",
            "THE INTERNET IS LOSING IT. And honestly, same.",
            "JUST IN from Hollywood. This is going to BREAK the internet.",
        ],
        "tone_guidance": (
            "- Lead with the MOST dramatic or shocking detail\n"
            "- Name-drop celebrities, shows, and platforms\n"
            "- Use social media energy: 'the internet is losing it', 'this broke the internet'\n"
            "- Keep it fun and gossipy but still factual\n"
            "- End with: 'Team [A] or Team [B]?' or 'Who's watching this?'"
        ),
        "visual_formula": "[Celebrity/Show] + [Dramatic Moment] + [Red Carpet/Stage Setting] + [Paparazzi Flash Lighting] + [Glamorous Bokeh]",
        "style_suffix": "Paparazzi photography, red carpet glamour, flash lighting, cinematic bokeh, vibrant colors, 8k celebrity portrait",
        "visual_emphasis": (
            "Glamour/High-Energy. Think: red carpet arrivals, concert stages with spotlights, "
            "movie premiere crowds, celebrity close-ups, flashing cameras, "
            "golden statuettes, neon-lit studios. Electric and vibrant."
        ),
        "urgency_interval": 4,
    },

    # ── Elon Musk ──────────────────────────────────────────────
    "elon_musk": {
        "name": "The Musk Decoder",
        "match_keywords": [
            "elon musk", "musk", "tesla", "spacex", "starlink",
            "neuralink", "boring company", "x.com", "twitter",
            "doge", "dogecoin", "mars", "starship", "cybertruck",
            "xai", "grok",
        ],
        "persona_instruction": (
            "You are the definitive Elon Musk analyst who tracks every tweet, "
            "every launch, and every controversy. You decode his moves with "
            "insider knowledge and tell people what it ACTUALLY means."
        ),
        "hook_patterns": [
            "ELON JUST DID IT AGAIN. And this time it's MASSIVE.",
            "BREAKING from SpaceX. Musk wasn't bluffing this time.",
            "STOP. Elon Musk just changed the game. Here's how.",
        ],
        "tone_guidance": (
            "- Lead with Musk's SPECIFIC action (tweeted, launched, announced, fired)\n"
            "- Reference the company involved (Tesla, SpaceX, xAI, X)\n"
            "- Decode the business strategy behind the move\n"
            "- Include market reaction or public response\n"
            "- End with: 'Genius or madness?' or 'Is Elon right about this?'"
        ),
        "visual_formula": "[Musk/Company] + [Latest Action] + [Factory/Launchpad/Office] + [Industrial Cinematic Lighting] + [Dramatic Wide Angle]",
        "style_suffix": "Industrial cinematic, SpaceX launch aesthetic, Tesla factory glow, dramatic wide angle, rocket exhaust, 8k hyper-real",
        "visual_emphasis": (
            "Industrial/Epic. Think: Starship on the launchpad at sunset, Tesla Gigafactory "
            "aerial shots, Cybertruck in dramatic landscapes, Musk silhouette against rocket fire, "
            "Neuralink brain chip close-up, X logo glowing. Monumental scale."
        ),
        "urgency_interval": 4,
    },

    # ── Humanoid Robots ────────────────────────────────────────
    "humanoid": {
        "name": "The Robot Correspondent",
        "match_keywords": [
            "humanoid", "robot", "robotics", "android", "bipedal",
            "boston dynamics", "figure", "optimus", "atlas", "digit",
            "1x", "agility robotics", "sanctuary ai", "apptronik",
            "autonomous", "embodied ai", "walking robot",
        ],
        "persona_instruction": (
            "You are a futurist robotics journalist who stands at the frontier "
            "between science fiction and reality. You report on humanoid robots "
            "with equal parts wonder and critical analysis."
        ),
        "hook_patterns": [
            "THE ROBOTS ARE HERE. This is NOT a movie.",
            "JUST IN. A humanoid robot just did something IMPOSSIBLE.",
            "STOP. Watch this robot. This changes your job forever.",
        ],
        "tone_guidance": (
            "- Lead with the MOST human-like capability the robot demonstrated\n"
            "- Name the specific robot model and company\n"
            "- Compare to what was 'impossible' just 12 months ago\n"
            "- Address the elephant: 'Will this take my job?'\n"
            "- End with: 'Are you excited or terrified?' or 'Which job is next?'"
        ),
        "visual_formula": "[Robot Model] + [Human-Like Action] + [Factory/Lab Setting] + [Cold Industrial Lighting] + [Slow Motion Detail]",
        "style_suffix": "Robotics cinematic, cold industrial lighting, motion detail, metallic textures, humanoid silhouette, 8k hyper-realistic",
        "visual_emphasis": (
            "Metallic/Uncanny. Think: humanoid robots walking in warehouses, close-up "
            "of robot hands grasping objects, glowing sensor eyes, metallic joints in "
            "motion, silhouettes against industrial backdrops, side-by-side with humans. "
            "Equal parts awe and unease."
        ),
        "urgency_interval": 5,
    },
}


# ── Default strategy (fallback for unmatched categories) ──────
DEFAULT_NEWS_STRATEGY: dict = {
    "name": "The Breaking News Anchor",
    "persona_instruction": (
        "You are a professional breaking news anchor for YouTube Shorts. "
        "Your videos break trending stories with urgency, accuracy, and "
        "punchy delivery that keeps viewers glued to the screen."
    ),
    "hook_patterns": [
        "BREAKING. This just happened and it changes everything.",
        "STOP SCROLLING. You need to hear this RIGHT NOW.",
        "JUST IN. Nobody is talking about this — but they should be.",
    ],
    "tone_guidance": (
        "- Lead with the single biggest fact\n"
        "- Use 'Pattern Interrupt' words: URGENT, JUST IN, BREAKING\n"
        "- Translate the news into personal impact within 5 seconds\n"
        "- End with a comment-driving question"
    ),
    "visual_formula": "[News Subject] + [Key Action] + [Relevant Setting] + [Photojournalistic Lighting] + [Motion Blur]",
    "style_suffix": "Photojournalistic, raw lighting, motion blur, 8k, sharp news aesthetic",
    "visual_emphasis": "",
    "urgency_interval": 5,
}


# ─────────────────────────────────────────────────────────────────
#  Registry
# ─────────────────────────────────────────────────────────────────

class NewsStrategyRegistry:
    """Registry that detects news category and returns the matching storytelling strategy."""

    @staticmethod
    def detect(category: str = "", title: str = "") -> dict:
        """
        Detect the best news strategy based on category and headline.

        Scoring:
          - Exact category key match → instant win (score = 100)
          - Keyword match in title → 1 point per keyword
          - Highest score wins; ties go to the first match

        Args:
            category: News category from the frontend tab (e.g. "technology")
            title: Article headline for keyword matching

        Returns:
            Strategy dict with persona, hooks, tone, visual formula, etc.
        """
        combined = f"{category} {title}".lower()

        best_strategy = None
        best_score = 0

        for key, strategy in NEWS_STRATEGIES.items():
            score = 0

            # Exact category match (normalized)
            cat_lower = category.lower().strip() if category else ""
            if cat_lower == key:
                score = 100  # instant win
            elif cat_lower.replace(" ", "_") == key:
                score = 100

            # Keyword scoring from title + category
            for kw in strategy["match_keywords"]:
                if kw.lower() in combined:
                    score += 1

            if score > best_score:
                best_score = score
                best_strategy = strategy

        if best_strategy and best_score > 0:
            logger.info(f"[NewsStrategy] Matched '{best_strategy['name']}' (score={best_score})")
            return best_strategy

        logger.info(f"[NewsStrategy] No match for '{category}' / '{title[:50]}' — using default")
        return DEFAULT_NEWS_STRATEGY

    @staticmethod
    def get_all_strategies() -> Dict[str, dict]:
        """Return all registered strategies including default."""
        result = dict(NEWS_STRATEGIES)
        result["default"] = DEFAULT_NEWS_STRATEGY
        return result

    @staticmethod
    def get_category_list() -> list:
        """Return list of supported category keys for frontend dropdown."""
        return list(NEWS_STRATEGIES.keys()) + ["default"]
