Accessibility Auditor - NVIDIA Hackathon 2025
==============================================

Built this in 2 hours during the NVIDIA & Vercel hackathon. It uses Nemotron to tell you what's wrong with your website's accessibility.

What It Does
-----------

Paste a screenshot or URL, get back actual accessibility issues. Not just "missing alt text" but real problems like "your grey-on-white text is unreadable" with actual fixes.

The cool part: it doesn't just list problems, it explains WHY they matter and gives you the exact code to fix them. Plus you can ask follow-up questions like "wait, what's ARIA?" and it'll explain without being condescending.

Features
--------

**Screenshot Analysis** - Drop an image, get accessibility audit  
**URL Analysis** - Enter a website, we'll grab it and analyze  
**NVIDIA Nemotron** - Using the 340B model because it actually understands context  
**Interactive Chat** - Ask dumb questions, get smart answers  
**Severity Levels** - Critical (users can't use it) vs Minor (annoying but works)  
**Real Code Fixes** - Copy-paste solutions, not vague suggestions

Quick Start (Get It Running)
----------------------------

**Need:**
- Python 3.8+
- NVIDIA API key from https://build.nvidia.com
- A browser

**Setup (literally 2 minutes):**

```bash
# Get dependencies
pip install fastapi uvicorn python-multipart python-dotenv httpx pillow pydantic

# Set your API key
cp .env.example .env
# Edit .env and add your NVIDIA_API_KEY

# Start backend
cd backend && python main.py

# Open frontend (new terminal)
cd frontend && python -m http.server 3000
```

Go to http://localhost:3000 and drop a screenshot. That's it.

How It Works
-----------

```
Frontend (React) → Backend (FastAPI) → NVIDIA Nemotron
     ↑                                         ↓
User drops image                      AI analyzes & returns fixes
```

Simple as that. Frontend sends image/URL, backend processes it, Nemotron does the thinking.

Tech Stack
---------

**Frontend**: React + TypeScript (because vanilla JS is chaos)  
**Backend**: FastAPI + Python (async all the things)  
**AI Model**: NVIDIA Nemotron-4-340B (via NIM API)  
**Image Processing**: Pillow (for screenshot handling)  
**HTTP Client**: httpx (better than requests for async)  
**Deployment**: Just Python, no Docker needed for hackathon

API Endpoints
------------

- `POST /audit/image` - Send an image, get accessibility audit
- `POST /audit/url` - Send a URL, we'll screenshot and analyze it
- `POST /chat` - Ask follow-up questions
- `GET /health` - Check if it's alive

Test It Out
----------

**Try these broken websites:**
- Sites with light grey text on white (contrast fail)
- Images with no alt text
- Tiny 10px fonts
- Forms without labels

**Ask the chat things like:**
- "How do I fix this contrast issue?"
- "What font size is actually readable?"
- "Show me good alt text examples"

The AI actually knows WCAG 2.1, Section 508, and ARIA standards, so it gives legit advice.

Troubleshooting
--------------

**"API key error"** - Check your .env file has the right NVIDIA key  
**"CORS blocked"** - Backend needs to be on port 8000  
**"Module not found"** - Run the pip install command again  
**"Port in use"** - Kill whatever's on 8000 or change the port  


Built For
--------

NVIDIA & Vercel "Agents for Impact" Hackathon - October 13, 2025

We actually built this in 2 hours. The hackathon was real, the time limit was brutal, but it works.

License
-------

MIT - Do whatever you want with it. Make the web more accessible.

