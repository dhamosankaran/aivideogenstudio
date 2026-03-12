# Personal Project Preferences (not checked into git)

## Start Commands
```bash
./clean_start.sh  # preferred — always use this (clears Python __pycache__ + Vite cache)
./start.sh        # fast start when caches are known-good
./stop.sh
```

## Dev URLs
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs

## Personal Notes
- Always check `backend/.env` at session start — keys expire
- SQLite DB lives at `backend/data/app.db`
- Generated videos: `backend/data/videos/`
- Generated images: `backend/data/images/`
