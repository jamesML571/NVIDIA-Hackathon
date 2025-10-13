# GitHub Repository Setup

## Option 1: Install GitHub CLI and create repository automatically

```bash
# Install GitHub CLI on macOS
brew install gh

# Authenticate with GitHub
gh auth login

# Create the repository and push
cd /Users/jamescunningham/imperium-ai-agent/nvidia-hackathon-accessibility-auditor
gh repo create nvidia-hackathon-accessibility-auditor --public --source=. --remote=origin --push
```

## Option 2: Manual setup (if you already created the repo on GitHub)

```bash
cd /Users/jamescunningham/imperium-ai-agent/nvidia-hackathon-accessibility-auditor

# Add the remote (replace YOUR_GITHUB_USERNAME with your actual username)
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/nvidia-hackathon-accessibility-auditor.git

# Push the code
git push -u origin main
```

## Option 3: Using SSH (if you have SSH keys configured)

```bash
cd /Users/jamescunningham/imperium-ai-agent/nvidia-hackathon-accessibility-auditor

# Add the remote with SSH (replace YOUR_GITHUB_USERNAME with your actual username)
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/nvidia-hackathon-accessibility-auditor.git

# Push the code
git push -u origin main
```

## Repository Contents

This repository contains:
- **Backend**: FastAPI server with NVIDIA NIM integration for AI-powered accessibility auditing
- **Frontend**: Interactive web interface for accessibility testing
- **Agent**: Browser extension for capturing website data
- **Log Viewer**: Dashboard for monitoring audit results

## Features
- Real-time accessibility scoring using NVIDIA's Llama 3.1 70B model
- Context-aware recommendations based on site type
- Numbered issue tracking with detailed fixes
- Interactive chat assistance for specific issues
- Comprehensive logging and analytics

## Tech Stack
- Backend: FastAPI, NVIDIA NIM API, Python
- Frontend: HTML, CSS, JavaScript
- AI Models: Meta Llama 3.1 70B via NVIDIA NIM