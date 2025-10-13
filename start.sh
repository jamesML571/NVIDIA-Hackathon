#!/bin/bash

# NVIDIA Hackathon Accessibility Auditor - Startup Script

echo "🚀 Starting NVIDIA Hackathon Accessibility Auditor..."
echo "================================================"

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
missing_deps=0

for package in fastapi uvicorn httpx pillow python-multipart python-dotenv; do
    if ! python3 -c "import $package" 2>/dev/null; then
        echo "  ⚠️  Missing: $package"
        missing_deps=1
    fi
done

if [ $missing_deps -eq 1 ]; then
    echo ""
    echo "📦 Installing missing dependencies..."
    pip3 install fastapi uvicorn httpx pillow python-multipart python-dotenv
fi

# Kill any existing process on port 8000
echo "🔄 Checking for existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the backend server
echo ""
echo "🚀 Starting backend server on http://localhost:8000"
echo "📊 API docs available at http://localhost:8000/docs"
echo ""

# Start uvicorn in the background
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Open the frontend in default browser
echo "🌐 Opening frontend in browser..."
open ../frontend/index.html 2>/dev/null || xdg-open ../frontend/index.html 2>/dev/null || echo "Please open frontend/index.html in your browser"

echo ""
echo "✅ Application started successfully!"
echo ""
echo "📝 Usage:"
echo "  - Frontend: file://$(pwd)/../frontend/index.html"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Wait for the backend process
wait $BACKEND_PID