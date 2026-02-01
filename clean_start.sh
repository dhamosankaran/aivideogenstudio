#!/bin/bash
# AIVideoGen Clean Startup Script
# Stops services, clears caches, and starts fresh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧹 Starting Clean Operations...${NC}"

# 1. Stop existing services
if [ -f "./stop.sh" ]; then
    echo "Stopping existing services..."
    ./stop.sh
else
    echo -e "${RED}Error: stop.sh not found!${NC}"
    exit 1
fi

# 2. Clear Backend Caches
echo "Clearing Backend Caches..."
find backend -type d -name "__pycache__" -exec rm -rf {} +
echo -e "${GREEN}✅ Python __pycache__ cleared${NC}"

# 3. Clear Frontend Caches
echo "Clearing Frontend Caches..."
if [ -d "frontend/node_modules/.vite" ]; then
    rm -rf frontend/node_modules/.vite
    echo -e "${GREEN}✅ Vite cache cleared${NC}"
else
    echo -e "${YELLOW}ℹ️  No Vite cache found to clear${NC}"
fi

# 4. Clear Logs (Optional, but good for "Clean" start)
# echo "Clearing Logs..."
# rm -f logs/*.log
# echo -e "${GREEN}✅ Logs cleared${NC}"

echo -e "${GREEN}✨ Clean complete! Starting services...${NC}"
echo ""

# 5. Start Services
./start.sh
