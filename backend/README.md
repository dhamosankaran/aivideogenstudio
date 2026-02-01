# AIVideoGen Backend

AI news video generation platform - Backend API

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
# At minimum you need:
# - GOOGLE_API_KEY (for Gemini - default LLM)
# - OPENAI_API_KEY (for OpenAI TTS - default TTS)
```

## Run

```bash
# Development
uvicorn app.main:app --reload

# Production
python -m app.main
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
