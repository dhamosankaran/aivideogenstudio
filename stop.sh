#!/bin/bash
# AIVideoGen Shutdown Script
# Stops both backend and frontend services

set -e

echo "🛑 Stopping AIVideoGen..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Stop backend
if [ -f .pids/backend.pid ]; then
    BACKEND_PID=$(cat .pids/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Force killing backend${NC}"
            kill -9 $BACKEND_PID
        fi
        
        echo -e "${GREEN}✅ Backend stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend not running${NC}"
    fi
    rm .pids/backend.pid
else
    echo -e "${YELLOW}⚠️  No backend PID file found${NC}"
fi

# Stop frontend
if [ -f .pids/frontend.pid ]; then
    FRONTEND_PID=$(cat .pids/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        
        # Wait for graceful shutdown
        for i in {1..10}; do
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                break
            fi
            sleep 1
        done
        
        # Force kill if still running
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "${YELLOW}⚠️  Force killing frontend${NC}"
            kill -9 $FRONTEND_PID
        fi
        
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend not running${NC}"
    fi
    rm .pids/frontend.pid
else
    echo -e "${YELLOW}⚠️  No frontend PID file found${NC}"
fi

echo ""
echo -e "${GREEN}✅ AIVideoGen stopped${NC}"
