#!/bin/bash

echo "GitHub Repository Setup Script"
echo "=============================="
echo ""

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo "You need to authenticate with GitHub first."
    echo "Running: gh auth login"
    echo ""
    echo "Please select:"
    echo "1. GitHub.com"
    echo "2. HTTPS (if prompted)"
    echo "3. Login with browser or paste authentication token"
    echo ""
    gh auth login
fi

echo ""
echo "Creating GitHub repository..."

# Create the repository
gh repo create nvidia-hackathon-accessibility-auditor \
    --public \
    --description "AI-powered web accessibility auditing tool using NVIDIA NIM API" \
    --source=. \
    --remote=origin \
    --push

echo ""
echo "Repository created and code pushed successfully!"
echo ""
echo "Your repository is now available at:"
echo "https://github.com/$(gh api user --jq .login)/nvidia-hackathon-accessibility-auditor"
echo ""
echo "✅ All tasks completed!"