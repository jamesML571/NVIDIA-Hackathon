"""
Accessibility Auditor API - NVIDIA Hackathon
Uses NVIDIA Nemotron for accessibility analysis and recommendations
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import io
import base64
import json
import re
from dotenv import load_dotenv
import httpx
from PIL import Image
import asyncio
from datetime import datetime
import json
from screenshot_capture import capture_screenshot_from_url, extract_html_from_url

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Accessibility Auditor API",
    description="AI-powered web accessibility analysis using NVIDIA Nemotron",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NEMOTRON_MODEL = os.getenv("NEMOTRON_MODEL", "nvidia/nemotron-4-340b-instruct")

class AccessibilityIssue(BaseModel):
    issue_type: str
    severity: str  # critical, major, minor
    description: str
    recommendation: str
    code_snippet: Optional[str] = None
    wcag_reference: Optional[str] = None

class AuditResponse(BaseModel):
    issues: List[AccessibilityIssue]
    summary: str
    total_issues: int
    critical_count: int
    major_count: int
    minor_count: int

class NemotronClient:
    """Client for NVIDIA Nemotron API"""
    
    def __init__(self):
        self.api_key = NVIDIA_API_KEY
        self.base_url = NVIDIA_BASE_URL
        self.model = NEMOTRON_MODEL
        
    async def analyze_accessibility(self, image_base64: str, html_content: Optional[str] = None) -> Dict:
        """
        Use Nemotron to analyze accessibility and psychological issues
        """
        prompt = self._build_accessibility_prompt(html_content)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are an expert in web accessibility (WCAG 2.1) and cognitive psychology for UX design.
                    Analyze both technical accessibility issues AND psychological/cognitive factors that affect user experience.
                    Consider visual hierarchy, cognitive load, emotional design, trust signals, and persuasion principles.
                    Provide actionable recommendations backed by both WCAG standards and psychological research."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 3000  # Increased for comprehensive analysis
        }
        
        if image_base64:
            payload["messages"][1]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return self._parse_nemotron_response(response.json())
            except Exception as e:
                print(f"Nemotron API error: {str(e)}")
                # Fallback to enhanced analysis
                return {
                    "issues": self._fallback_analysis(),
                    "scores": {},
                    "summary": "Analysis performed with fallback data",
                    "top_priorities": []
                }
    
    def _build_accessibility_prompt(self, html_content: Optional[str]) -> str:
        prompt = """You are an accessibility + visual-cognition agent. Analyze the uploaded webpage screenshot for both WCAG accessibility issues and human-factors/psychology problems that reduce comprehension, trust, and usability.

Check across:
- WCAG/A11Y: low contrast, missing alt text, unclear link labels, unreadable/hidden UI, non-sequential headings, small or dense text, missing focus states, poor keyboard navigation.
- Cognitive Load: clutter, weak chunking, too many focal points, unclear hierarchy, dense paragraphs.
- Color & Emotion: poor color harmony, over-saturation, off-brand tone, color misuse for CTAs.
- Typography: inconsistent font pairing, improper sizing, low readability, poor contrast, alignment issues.
- Navigation: ambiguous next steps, disorganized menus, non-sticky headers, lack of anchors.
- Trust/Emotion: stock imagery, weak credibility cues, misaligned facial orientation.
- Persuasion: missing progress indicators, poor anchoring, unclear CTA language.
- Layout & Motion: grid imbalance, excessive animation, poor white-space ratio.
- Brand Consistency: inconsistent color palette, icons, or hover states.

Return a structured JSON with these categories:
{
  "summary": "Brief overview of accessibility and visual appeal",
  "scores": {
    "cognitive_load": 0-100,
    "visual_hierarchy": 0-100,
    "navigation": 0-100,
    "balance": 0-100,
    "accessibility_wcag": 0-100,
    "emotional_tone": 0-100,
    "brand_consistency": 0-100
  },
  "issues": [
    {
      "category": "[A11Y] or [Psych]",
      "issue_type": "Specific issue name",
      "severity": "critical/major/minor",
      "description": "What's wrong",
      "impact": "Why it matters for users",
      "recommendation": "How to fix it",
      "code_snippet": "Optional code example",
      "wcag_reference": "If applicable"
    }
  ],
  "top_priorities": ["List of top 5 fixes in order of importance"]
}"""
        
        if html_content:
            prompt += f"\n\nHTML Content:\n{html_content[:2000]}"  # Limit HTML size
        
        return prompt
    
    def _parse_nemotron_response(self, response: Dict) -> Dict:
        """Parse Nemotron response into structured issues and scores"""
        try:
            content = response["choices"][0]["message"]["content"]
            
            # Try to parse as JSON first
            if content.strip().startswith("[") or content.strip().startswith("{"):
                parsed_data = json.loads(content)
                
                # Handle enhanced format with scores
                if isinstance(parsed_data, dict):
                    if "issues" in parsed_data:
                        issues_data = parsed_data["issues"]
                        scores = parsed_data.get("scores", {})
                        summary = parsed_data.get("summary", "")
                        top_priorities = parsed_data.get("top_priorities", [])
                    else:
                        # Legacy format
                        issues_data = [parsed_data]
                        scores = {}
                        summary = ""
                        top_priorities = []
                else:
                    issues_data = parsed_data if isinstance(parsed_data, list) else [parsed_data]
                    scores = {}
                    summary = ""
                    top_priorities = []
            else:
                # Parse text response into structured format
                issues_data = self._parse_text_response(content)
                scores = {}
                summary = ""
                top_priorities = []
            
            issues = []
            for item in issues_data:
                # Handle both [A11Y] and [Psych] categories
                category = item.get("category", "")
                issue_type = item.get("issue_type", "Unknown Issue")
                
                # Combine category with issue type for display
                if category:
                    issue_type = f"{category} {issue_type}"
                
                issues.append(AccessibilityIssue(
                    issue_type=issue_type,
                    severity=item.get("severity", "minor"),
                    description=item.get("description", ""),
                    recommendation=item.get("recommendation", ""),
                    code_snippet=item.get("code_snippet"),
                    wcag_reference=item.get("wcag_reference", item.get("impact", ""))
                ))
            
            return {
                "issues": issues,
                "scores": scores,
                "summary": summary,
                "top_priorities": top_priorities
            }
        except Exception as e:
            print(f"Error parsing response: {e}")
            return {
                "issues": self._fallback_analysis(),
                "scores": {},
                "summary": "Analysis completed with fallback data",
                "top_priorities": []
            }
    
    def _parse_text_response(self, text: str) -> List[Dict]:
        """Parse unstructured text response into issues"""
        # Simple parser for text responses
        issues = []
        lines = text.split("\n")
        current_issue = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_issue:
                    issues.append(current_issue)
                    current_issue = {}
                continue
            
            if "issue" in line.lower() or "problem" in line.lower():
                if current_issue:
                    issues.append(current_issue)
                current_issue = {"description": line}
            elif "severity" in line.lower():
                if "critical" in line.lower():
                    current_issue["severity"] = "critical"
                elif "major" in line.lower():
                    current_issue["severity"] = "major"
                else:
                    current_issue["severity"] = "minor"
            elif "recommend" in line.lower() or "fix" in line.lower():
                current_issue["recommendation"] = line
            elif "wcag" in line.lower():
                current_issue["wcag_reference"] = line
        
        if current_issue:
            issues.append(current_issue)
        
        return issues
    
    def _fallback_analysis(self) -> List[AccessibilityIssue]:
        """Provide basic accessibility checks as fallback"""
        return [
            AccessibilityIssue(
                issue_type="API Connection Issue",
                severity="major",
                description="Could not connect to NVIDIA Nemotron API for full analysis",
                recommendation="Please check API credentials and try again. Basic checks were performed.",
                wcag_reference="N/A"
            ),
            AccessibilityIssue(
                issue_type="Color Contrast",
                severity="major",
                description="Ensure text has sufficient contrast against background",
                recommendation="Use a contrast ratio of at least 4.5:1 for normal text and 3:1 for large text",
                code_snippet="color: #000; background-color: #fff;",
                wcag_reference="WCAG 2.1 - 1.4.3"
            ),
            AccessibilityIssue(
                issue_type="Alt Text",
                severity="critical",
                description="Images should have descriptive alt text",
                recommendation="Add meaningful alt attributes to all images",
                code_snippet='<img src="image.jpg" alt="Description of image">',
                wcag_reference="WCAG 2.1 - 1.1.1"
            )
        ]

# Initialize Nemotron client
nemotron_client = NemotronClient()

@app.get("/")
async def root():
    return {
        "message": "Accessibility Auditor API - NVIDIA Hackathon",
        "model": "Powered by NVIDIA Nemotron",
        "endpoints": {
            "/audit/image": "POST - Upload image for analysis",
            "/audit/url": "POST - Analyze URL",
            "/health": "GET - Health check"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "nemotron_configured": bool(NVIDIA_API_KEY),
        "model": NEMOTRON_MODEL
    }

@app.post("/audit/image")
async def audit_image(file: UploadFile = File(...)):
    """
    Analyze uploaded image for accessibility and psychological issues using NVIDIA Nemotron
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read and encode image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to base64
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Analyze with Nemotron (returns enhanced format)
        analysis_result = await nemotron_client.analyze_accessibility(image_base64)
        
        # Extract components from enhanced analysis
        issues = analysis_result.get("issues", [])
        scores = analysis_result.get("scores", {})
        enhanced_summary = analysis_result.get("summary", "")
        top_priorities = analysis_result.get("top_priorities", [])
        
        # Calculate summary statistics
        critical_count = sum(1 for i in issues if i.severity == "critical")
        major_count = sum(1 for i in issues if i.severity == "major")
        minor_count = sum(1 for i in issues if i.severity == "minor")
        
        # Build comprehensive summary
        if enhanced_summary:
            summary = enhanced_summary
        else:
            summary = f"Found {len(issues)} issues: {critical_count} critical, {major_count} major, {minor_count} minor"
        
        # Return enhanced response format
        return {
            "issues": [issue.dict() for issue in issues],
            "summary": summary,
            "total_issues": len(issues),
            "critical_count": critical_count,
            "major_count": major_count,
            "minor_count": minor_count,
            "scores": scores,
            "top_priorities": top_priorities
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/audit/url")
async def audit_url(url: str = Form(...)):
    """
    Analyze website URL for accessibility issues by capturing screenshot
    """
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        # Capture screenshot from URL
        screenshot_base64 = await capture_screenshot_from_url(url)
        
        if not screenshot_base64:
            # Fallback if screenshot capture fails
            return {
                "issues": [
                    {
                        "issue_type": "Screenshot Capture Failed",
                        "severity": "major",
                        "description": f"Could not capture screenshot from {url}. Please ensure Pyppeteer is installed or upload a screenshot directly.",
                        "recommendation": "Install Pyppeteer with: pip install pyppeteer",
                        "wcag_reference": "N/A"
                    }
                ],
                "summary": "Screenshot capture failed. Please upload an image directly.",
                "total_issues": 1,
                "critical_count": 0,
                "major_count": 1,
                "minor_count": 0,
                "scores": {},
                "top_priorities": []
            }
        
        # Extract HTML for additional context
        html_content = await extract_html_from_url(url)
        
        # Analyze with Nemotron (same as image analysis)
        analysis_result = await nemotron_client.analyze_accessibility(screenshot_base64, html_content)
        
        # Extract components from enhanced analysis
        issues = analysis_result.get("issues", [])
        scores = analysis_result.get("scores", {})
        enhanced_summary = analysis_result.get("summary", "")
        top_priorities = analysis_result.get("top_priorities", [])
        
        # Calculate summary statistics
        critical_count = sum(1 for i in issues if i.severity == "critical")
        major_count = sum(1 for i in issues if i.severity == "major")
        minor_count = sum(1 for i in issues if i.severity == "minor")
        
        # Build comprehensive summary
        if enhanced_summary:
            summary = f"Analysis of {url}: {enhanced_summary}"
        else:
            summary = f"Found {len(issues)} issues on {url}: {critical_count} critical, {major_count} major, {minor_count} minor"
        
        # Return enhanced response format
        return {
            "issues": [issue.dict() for issue in issues],
            "summary": summary,
            "total_issues": len(issues),
            "critical_count": critical_count,
            "major_count": major_count,
            "minor_count": minor_count,
            "scores": scores,
            "top_priorities": top_priorities,
            "analyzed_url": url
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing URL: {str(e)}")

@app.post("/chat")
async def chat_about_accessibility(question: str = Form(...), context: Optional[str] = Form(None)):
    """
    Interactive chat endpoint for follow-up questions about accessibility fixes
    """
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are an accessibility expert. Answer questions about web accessibility,
    WCAG compliance, and provide code examples for fixing accessibility issues.
    Be concise but thorough in your explanations."""
    
    user_prompt = question
    if context:
        user_prompt = f"Context: {context}\n\nQuestion: {question}"
    
    payload = {
        "model": NEMOTRON_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 500
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return {
                "answer": result["choices"][0]["message"]["content"],
                "model": NEMOTRON_MODEL
            }
        except Exception as e:
            return {
                "answer": "I can help you with accessibility questions. Please ensure the API is configured correctly.",
                "error": str(e)
            }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)