# 🔍 Accessibility Auditor - NVIDIA Hackathon 2025

**Agents for Impact** - Building AI agents that make the web accessible to everyone

##  Hackathon Focus
- **Event**: NVIDIA & Vercel "Agents for Impact" Hackathon
- **Date**: October 13, 2025
- **Time Limit**: 2 hours
- **Featured Model**: NVIDIA Nemotron-4-340B (via NIM API)

## 🎯 Project Overview

An AI-powered accessibility auditor that analyzes web interfaces for WCAG compliance issues and provides actionable recommendations. Users can upload screenshots or enter URLs to get instant accessibility analysis powered by NVIDIA's Nemotron model.

### Key Features
- 📸 **Screenshot Analysis**: Upload images for instant accessibility audit
- 🔗 **URL Analysis**: Enter website URLs for accessibility checking
- 🤖 **NVIDIA Nemotron Integration**: Leverages state-of-the-art LLM for intelligent analysis
- 💬 **Interactive Chat**: Ask follow-up questions about accessibility fixes
- 📊 **Severity Classification**: Issues categorized as Critical, Major, or Minor
- ✅ **Actionable Recommendations**: Get specific code snippets and WCAG references

## 🚀 Quick Start (2-Hour Sprint)

### Prerequisites
- Python 3.8+
- NVIDIA NIM API Access (get your key at https://build.nvidia.com)
- Modern web browser

### 1️⃣ Setup Backend (5 minutes)

```bash
# Clone or navigate to project
cd nvidia-hackathon-accessibility-auditor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn python-multipart python-dotenv httpx pillow pydantic

# Create .env file from example
cp .env.example .env

# Add your NVIDIA API key to .env
# NVIDIA_API_KEY=your_actual_api_key_here
```

### 2️⃣ Start the Backend Server

```bash
cd backend
python main.py
```

Server will run at `http://localhost:8000`

### 3️⃣ Launch Frontend

Simply open `frontend/index.html` in your browser, or serve it:

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000
```

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  React Frontend ├────►│  FastAPI Backend ├────►│ NVIDIA Nemotron │
│                 │     │                  │     │    (NIM API)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                         │
        │                       │                         │
    Upload Image           Process & Analyze        AI-Powered Analysis
    Enter URL              Accessibility             Recommendations
    Chat Interface         Issue Detection           Code Snippets
```

## 🔑 NVIDIA Models Used

1. **Nemotron-4-340B-Instruct** (Primary)
   - Accessibility analysis and reasoning
   - Code generation for fixes
   - WCAG compliance checking

2. **Vision Models** (Optional enhancement)
   - FLUX.1 for visual analysis
   - Kosmos-2 for multimodal understanding

## 📝 API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /audit/image` - Analyze uploaded image
- `POST /audit/url` - Analyze website URL
- `POST /chat` - Interactive chat about accessibility

## 🎨 Demo Scenarios

### Test Images
1. Low contrast text websites
2. Images without alt text
3. Small font sizes
4. Poor color combinations
5. Missing form labels

### Sample Questions for Chat
- "How do I fix the color contrast issue?"
- "What's the WCAG standard for font sizes?"
- "Can you show me an example of proper alt text?"
- "How do I make my forms more accessible?"

## 🏆 Judging Criteria Alignment

✅ **Agentic Reasoning**: Multi-stage analysis pipeline (detect → explain → recommend)  
✅ **NVIDIA Technology**: Showcases Nemotron model capabilities  
✅ **Real Impact**: Makes web more accessible to users with disabilities  
✅ **Working Demo**: Full MVP in 2 hours  

## 📚 Accessibility Standards Referenced

- WCAG 2.1 Level AA Compliance
- Section 508 Standards
- ADA Web Accessibility Guidelines
- ARIA Best Practices

## 🚨 Troubleshooting

1. **API Key Issues**: Ensure your NVIDIA API key is correctly set in `.env`
2. **CORS Errors**: Make sure backend is running on port 8000
3. **Module Not Found**: Install all required Python packages
4. **Port Already in Use**: Change PORT in .env or kill existing process

## 💡 Future Enhancements (Post-Hackathon)

- [ ] Playwright/Puppeteer integration for automatic screenshots
- [ ] RAG system with accessibility knowledge base
- [ ] Batch analysis for multiple pages
- [ ] Export reports as PDF
- [ ] Browser extension
- [ ] Real-time monitoring

## 👥 Team

Built with ❤️ for the NVIDIA Hackathon 2025

## 📄 License

MIT License - Use freely for accessibility improvements!

---

