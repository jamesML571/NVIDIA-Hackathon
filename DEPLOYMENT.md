# 🚀 Deployment Instructions - NVIDIA Hackathon Accessibility Auditor

## Quick Start (Recommended)

Simply run the startup script:

```bash
cd /Users/jamescunningham/imperium-ai-agent/nvidia-hackathon-accessibility-auditor
bash start.sh
```

This will:
1. Check and install dependencies
2. Start the backend server
3. Open the frontend in your browser
4. Show you the URLs to access everything

## Manual Deployment

If you prefer to start components manually:

### 1. Backend Server

```bash
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend

Open in your browser:
```
file:///Users/jamescunningham/imperium-ai-agent/nvidia-hackathon-accessibility-auditor/frontend/index.html
```

Or serve it with Python:
```bash
cd frontend
python3 -m http.server 3000
# Then open http://localhost:3000
```

## Features Working

✅ **Image Upload**: Upload screenshots or designs for accessibility analysis
✅ **URL Analysis**: Enter website URLs for automatic screenshot and analysis  
✅ **NVIDIA Models Integration**:
  - Nemotron-4-340B for enhanced reasoning
  - Llama-3.2-11B Vision for visual analysis
  - Llama-3.2-3B for chat functionality
✅ **Context-Specific Insights**: "Why this matters" tailored to your specific content
✅ **Code Fixes**: Specific CSS/HTML fixes for each issue found

## Access Points

- **Frontend**: http://localhost:3000 (or file:// URL)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Troubleshooting

### Port Already in Use
```bash
lsof -ti:8000 | xargs kill -9
```

### Missing Dependencies
```bash
pip3 install fastapi uvicorn httpx pillow python-multipart python-dotenv
```

### Python Not Found
Use `python3` instead of `python`

### Frontend Not Loading
- Ensure backend is running on port 8000
- Check browser console for errors
- Try refreshing the page

## Verification

To verify everything is working:
1. Go to http://localhost:8000/health - should show "healthy"
2. Open the frontend and try uploading an image
3. Check http://localhost:8000/docs for API documentation

## Models Being Used

1. **NVIDIA Nemotron-4-340B-Instruct** (Primary)
   - Deep accessibility reasoning
   - Code generation
   - Business impact analysis

2. **Meta Llama-3.2-11B Vision**
   - Visual content analysis
   - Screenshot understanding

3. **Meta Llama-3.2-3B**
   - Chat interactions
   - Quick Q&A responses

The system automatically chains these models for comprehensive analysis!