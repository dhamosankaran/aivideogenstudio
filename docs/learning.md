# AIVideoGen - Lessons Learned

This document captures lessons learned during development to help future contributors avoid common pitfalls.

---

## 2026-02-01: Python 3.13 Compatibility Issues

### Problem
Backend failed to start with `ModuleNotFoundError` errors when using Python 3.13.

### Root Cause
Python 3.13 removed the `audioop` module from the standard library (PEP 594 - deprecated batteries). The `pydub` library depends on `audioop`.

### Solution
Install the `audioop-lts` package which provides a drop-in replacement:
```bash
pip install audioop-lts
```

### Prevention
- Added `audioop-lts` to `requirements.txt` with a comment explaining Python 3.13+ compatibility
- Created `backend/SETUP.md` with troubleshooting guide

---

## 2026-02-01: Missing Dependencies Not in requirements.txt

### Problem
Several dependencies were installed manually but not added to `requirements.txt`:
- `openai-whisper` - For Whisper speech recognition service
- `newsapi-python` - For News API integration
- `audioop-lts` - For Python 3.13 compatibility

### Root Cause
Dependencies were installed during development but not tracked in requirements file.

### Solution
Added all missing dependencies to `requirements.txt` with explanatory comments:
```
openai-whisper  # Speech recognition (Whisper model)
newsapi-python  # News API client
audioop-lts     # Required for pydub on Python 3.13+
```

### Prevention
- **Always run `pip freeze` after installing new packages** to verify they're tracked
- Use comments in `requirements.txt` to explain non-obvious dependencies
- Test fresh venv setup periodically

---

## 2026-02-01: Git Repository Setup in Subdirectory

### Problem
The `aivideogenstudio` folder was inside a parent git repository, causing untracked file warnings.

### Root Cause
The working directory was a subdirectory of a larger git repo.

### Solution
Initialized a new git repository specifically in the `aivideogenstudio` directory:
```bash
cd aivideogenstudio
git init
git remote add origin https://github.com/dhamosankaran/aivideogenstudio
git add .
git commit -m "Initial commit"
git branch -m master main
git push -u origin main
```

### Prevention
- Check `git rev-parse --show-toplevel` before git operations to understand repository context
- Keep project repositories isolated where possible

---

## Best Practices Established

1. **Dependency Management**
   - Document all dependencies in `requirements.txt` with comments
   - Include compatibility packages for newer Python versions
   - Test on fresh venv periodically

2. **Documentation**
   - Maintain `SETUP.md` in backend directory
   - Keep `learning.md` updated with issues encountered
   - Use clear troubleshooting sections

3. **Startup Scripts**
   - Use `clean_start.sh` for fresh starts (clears caches)
   - Use `start.sh` for regular starts
   - Use `stop.sh` to cleanly stop services

---

## 2026-02-01: YouTube Analysis JSON Truncation

### Problem
YouTube transcript analysis failed with "Invalid JSON: EOF while parsing a string" error. The LLM response was being cut off mid-JSON.

### Root Cause
1. Long transcripts (37+ minute videos) produced prompts too large
2. `max_tokens=4000` was insufficient for the expected JSON response
3. The LLM generated very long `transcript_text` fields in the output

### Solution
Applied multi-pronged fix in `youtube_transcript_service.py`:
```python
# 1. Truncate transcripts > 15000 chars
if len(transcript_text) > 15000:
    transcript_text = transcript_text[:15000] + "\n...[truncated]"

# 2. Increased max_tokens from 4000 to 8000
max_tokens=8000

# 3. Added retry logic with fewer insights
for attempt in range(2):
    if attempt == 1:
        # Request only 3 insights on retry
        prompt = build_prompt(max_insights=3)

# 4. Updated prompt to request shorter transcript_text (max 200 chars)
```

### Prevention
- Always truncate large inputs to LLMs to prevent oversized prompts
- Use generous `max_tokens` for structured JSON responses
- Implement retry logic with simplified prompts for robustness
- Request shorter/smaller outputs in the prompt itself

---

## 2026-02-07: Validation-First Development Strategy

### Problem
Temptation to add ElevenLabs TTS (premium feature) before validating the core product with real users.

### Root Cause
Classic startup mistake: optimizing **production quality** before validating **content quality**. We had a complete video pipeline but 0 videos posted to YouTube.

### CTO Strategic Decision
**Don't build features until you have data proving the need.**

| Question | Answer |
|----------|--------|
| Is ElevenLabs TTS 20x better? | Unknown - no audience feedback yet |
| Will it increase watch time? | Unknown - no videos posted |
| Where is the actual bottleneck? | Unknown - need 15+ videos to measure |

### Better Approach
1. **Generate 15 videos** with existing pipeline ($0.45 total)
2. **Post to YouTube** and track metrics
3. **Analyze** what's actually the bottleneck
4. **Then** decide: TTS quality? Thumbnails? Scripts? Distribution?

### Key Learnings
- **Stop building. Start shipping.** - Complete pipeline means nothing without validation
- **Use data, not intuition** - "Better voice = more views" is an assumption, not a fact
- **Cheap experiments first** - Use $0.019/video OpenAI TTS before $0.375/video ElevenLabs
- **Time is a cost too** - 20 dev hours for unvalidated features vs 3 hours for 15 real videos

### Prevention
Before any new feature, ask:
1. Do I have data proving this is a bottleneck?
2. Can I validate the assumption cheaper/faster?
3. Have I shipped anything to get user feedback?

---

## 2026-02-07: Environment Variable Audit

### Problem
`.env` file had `DEFAULT_TTS_PROVIDER=openai` but `OPENAI_API_KEY=your_openai_api_key_here` (placeholder value). TTS would fail at runtime.

### Root Cause
- Template `.env.example` values copied but not updated
- No startup validation of required API keys
- CTO didn't audit `.env` early enough in session

### Solution
1. Change `DEFAULT_TTS_PROVIDER=google` (since Google API key is valid)
2. Or add a real OpenAI API key

### Prevention
- **Always audit `.env` at session start** - Part of CTO checklist
- **Add startup validation** in `main.py` to verify required keys are set
- **Don't use placeholder strings** - Use empty string or omit entirely
- **Cross-check** - If `DEFAULT_TTS_PROVIDER=X`, then `X_API_KEY` must be valid

---

## Best Practices Established (Updated)

1. **Dependency Management**
   - Document all dependencies in `requirements.txt` with comments
   - Include compatibility packages for newer Python versions
   - Test on fresh venv periodically

2. **Documentation**
   - Maintain `SETUP.md` in backend directory
   - Keep `learning.md` updated with issues encountered
   - Use clear troubleshooting sections
   - **NEW**: Consolidate all docs under `docs/` folder

3. **Startup Scripts**
   - Use `clean_start.sh` for fresh starts (clears caches)
   - Use `start.sh` for regular starts
   - Use `stop.sh` to cleanly stop services

4. **Strategic Decision Making** (NEW)
   - Ship first, optimize second
   - Use data to drive feature decisions
   - Validate core value proposition before adding premium features
   - Track assumptions vs facts

5. **Environment Configuration** (NEW)
   - Audit `.env` at start of each session
   - Cross-check provider settings with API keys
   - Never use placeholder strings in production `.env`
