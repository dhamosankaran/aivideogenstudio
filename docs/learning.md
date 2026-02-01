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
