#!/bin/bash

# Ultimate Accessibility Auditor Launch Script
# Complete system setup and launch

set -e

echo "🚀 Launching Ultimate Accessibility Auditor System"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Function to kill process on port
kill_port() {
    if check_port $1; then
        echo -e "${YELLOW}Port $1 is in use. Stopping existing process...${NC}"
        kill $(lsof -t -i:$1) 2>/dev/null || true
        sleep 2
    fi
}

echo -e "${BLUE}Step 1: Checking dependencies...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Step 2: Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade pip
pip install --upgrade pip --quiet

# Install backend dependencies
echo -e "${BLUE}Step 3: Installing backend dependencies...${NC}"
pip install -r backend/requirements.txt --quiet
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Check .env file
echo -e "${BLUE}Step 4: Checking configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with your NVIDIA API key"
    echo "Copy .env.example to .env and add your API key"
    exit 1
fi

# Source the .env file to check API key
if grep -q "NVIDIA_API_KEY=nvapi-" .env; then
    echo -e "${GREEN}✓ NVIDIA API key configured${NC}"
else
    echo -e "${RED}Error: NVIDIA API key not found in .env${NC}"
    echo "Please add your NVIDIA API key to the .env file"
    exit 1
fi

# Kill existing processes on ports
echo -e "${BLUE}Step 5: Checking ports...${NC}"
kill_port 8000

# Start backend server
echo -e "${BLUE}Step 6: Starting backend server...${NC}"
cd backend

# Use the genuine backend for real analysis
if [ ! -f "main_genuine.py" ]; then
    # Fall back to ultimate if genuine doesn't exist
    if [ ! -f "main_ultimate.py" ]; then
        echo -e "${RED}Error: Backend files not found!${NC}"
        exit 1
    fi
    BACKEND_FILE="main_ultimate.py"
else
    BACKEND_FILE="main_genuine.py"
fi

# Copy parent .env if not exists in backend
if [ ! -f ".env" ]; then
    cp ../.env .env
fi

# Start backend in background
echo -e "${YELLOW}Starting backend server on http://localhost:8000${NC}"
echo -e "${BLUE}Using: $BACKEND_FILE (genuine analysis)${NC}"
python3 $BACKEND_FILE > server.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to start...${NC}"
for i in {1..30}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
        echo -e "${GREEN}✓ Backend server is running${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Backend failed to start${NC}"
        echo "Check backend/server.log for errors"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Open frontend
echo -e "${BLUE}Step 7: Opening frontend...${NC}"
cd ../frontend

# Check if ultimate frontend exists
if [ ! -f "index_ultimate.html" ]; then
    echo -e "${RED}Error: index_ultimate.html not found!${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Get the full path
FRONTEND_PATH="file://$SCRIPT_DIR/frontend/index_ultimate.html"

# Open in default browser
echo -e "${YELLOW}Opening frontend in browser...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$FRONTEND_PATH"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$FRONTEND_PATH"
else
    echo -e "${YELLOW}Please open in your browser: $FRONTEND_PATH${NC}"
fi

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Ultimate Accessibility Auditor is running!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}Frontend UI:${NC} $FRONTEND_PATH"
echo -e "${BLUE}API Docs:${NC}    http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Test URLs to try:${NC}"
echo "  • https://github.com (Developer platform)"
echo "  • https://amazon.com (E-commerce)"
echo "  • https://netflix.com (Streaming)"
echo "  • https://stackoverflow.com (Q&A platform)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

# Keep script running and handle shutdown
trap "echo -e '\n${YELLOW}Shutting down...${NC}'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM

# Wait for backend process
wait $BACKEND_PID