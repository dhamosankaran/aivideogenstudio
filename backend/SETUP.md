# Backend Setup Guide

## Prerequisites
- Python 3.11+ (Python 3.13 supported with compatibility packages)
- Node.js 18+ (for frontend)

## Quick Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Python 3.13+ Compatibility

If using Python 3.13 or later, the following packages are required:
- `audioop-lts`: The `audioop` module was removed from Python 3.13 stdlib. This package provides compatibility for `pydub`.

These are already included in `requirements.txt`.

## Running the Application

From the project root:
```bash
./clean_start.sh  # Stops services, clears caches, starts fresh
./start.sh        # Start services
./stop.sh         # Stop services
```

## Troubleshooting

### ModuleNotFoundError: No module named 'audioop' or 'pyaudioop'
```bash
pip install audioop-lts
```

### ModuleNotFoundError: No module named 'whisper'
```bash
pip install openai-whisper
```

### ModuleNotFoundError: No module named 'newsapi'
```bash
pip install newsapi-python
```

## Environment Variables

Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```
