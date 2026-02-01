#!/bin/bash
# AIVideoGen Startup Script
# Starts both backend and frontend services

set -e

echo "🚀 Starting AIVideoGen..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create PID directory
mkdir -p .pids

# Check if services are already running
if [ -f .pids/backend.pid ] && kill -0 $(cat .pids/backend.pid) 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Backend already running (PID: $(cat .pids/backend.pid))${NC}"
else
    # Start backend
    echo "Starting backend..."
    cd backend
    source venv/bin/activate
    nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../.pids/backend.pid
    cd ..
    echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
    
    # Wait for backend to be ready
    echo "Waiting for backend..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend is healthy${NC}"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Backend failed to start${NC}"
            exit 1
        fi
    done
fi

# Check if frontend is already running
if [ -f .pids/frontend.pid ] && kill -0 $(cat .pids/frontend.pid) 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Frontend already running (PID: $(cat .pids/frontend.pid))${NC}"
else
    # Start frontend
    echo "Starting frontend..."
    cd frontend
    nohup npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.pids/frontend.pid
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
fi

echo ""
echo -e "${GREEN}🎉 AIVideoGen is running!${NC}"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend:  tail -f logs/backend.log"
echo "  Frontend: tail -f logs/frontend.log"
echo ""
echo "To stop: ./stop.sh"
