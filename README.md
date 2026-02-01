# AIVideoGen

Automated AI news video generation platform with web dashboard.

## Features

- 🤖 Multi-provider LLM support (Gemini 2.0 Flash, OpenAI, Claude)
- 🎤 Multi-provider TTS (Google Cloud TTS, OpenAI TTS, ElevenLabs)
- 📰 RSS feed aggregation and web scraping
- 🎬 Automated video composition with FFmpeg
- 🖥️ React web dashboard for control
- 💰 Budget-conscious: <$5/month for daily videos

## Quick Start

### One-Command Startup
```bash
./start.sh
```

This will:
- Start the backend (FastAPI on port 8000)
- Start the frontend (Vite on port 5173)
- Wait for backend health check
- Display service URLs

### Manual Startup

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Shutdown
```bash
./stop.sh
```

## Configuration

Edit `backend/.env` and add at minimum:
- `GOOGLE_API_KEY` - For Gemini (default LLM)
- `OPENAI_API_KEY` - For OpenAI TTS (default TTS)

See `.env.example` for all options.

## Project Structure

```
AIVideoGen/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # HTTP endpoints
│   │   ├── services/ # Business logic
│   │   ├── providers/# LLM/TTS provider implementations
│   │   └── models/   # Database models
│   └── data/         # Generated content storage
│
├── frontend/         # React + Vite frontend
│   └── src/
│       ├── pages/    # Dashboard,Settings, etc.
│       └── components/
│
└── docs/             # Documentation
```

## Development Workflow

This project uses structured AI workflows:
- `/create-issue` - Capture ideas
- `/exploration` - Understand problems
- `/create-plan` - Create blueprints
- `/execute` - Build features

See `.agent/workflows/` for details.

## License

MIT
