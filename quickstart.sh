#!/bin/bash

# NVIDIA Hackathon - Accessibility Auditor Quick Start Script
# Run this to set up everything in under 2 minutes!

echo "🚀 NVIDIA Hackathon - Accessibility Auditor Setup"
echo "================================================"
echo ""

# Check Python
echo "✅ Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3.8+"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing required packages..."
pip install --quiet fastapi uvicorn python-multipart python-dotenv httpx pillow pydantic

# Copy .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Add your NVIDIA API key to .env file"
    echo "   Edit .env and replace 'your_nvidia_api_key_here' with your actual key"
    echo "   Get your key at: https://build.nvidia.com"
    echo ""
fi

echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Add your NVIDIA API key to .env file"
echo "2. Run the backend: cd backend && python main.py"
echo "3. Open frontend/index.html in your browser"
echo ""
echo "Good luck with the hackathon! 🏆"