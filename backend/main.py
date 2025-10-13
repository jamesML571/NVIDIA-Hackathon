"""
Accessibility Auditor - Production Backend with NVIDIA NIM
Optimized for accurate scoring and context-aware recommendations
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional
import asyncio
from PIL import Image
import io
import base64
import re
from bs4 import BeautifulSoup
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Accessibility Auditor API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NVIDIA API Configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Using Llama 3.1 70B for better context understanding and scoring
PRIMARY_MODEL = "meta/llama-3.1-70b-instruct"

class AccessibilityAnalyzer:
    """Production analyzer with NVIDIA NIM for improved scoring"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def analyze_with_context(self, url: str, html_content: str, screenshot: Optional[bytes] = None) -> Dict:
        """Perform context-aware accessibility analysis"""
        
        # Parse HTML for structural analysis
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract key metrics
        metrics = {
            "images_total": len(soup.find_all('img')),
            "images_without_alt": len([img for img in soup.find_all('img') if not img.get('alt')]),
            "forms": len(soup.find_all('form')),
            "headings": {
                "h1": len(soup.find_all('h1')),
                "h2": len(soup.find_all('h2')),
                "h3": len(soup.find_all('h3'))
            },
            "aria_landmarks": len(soup.find_all(attrs={"role": True})),
            "buttons_without_text": len([btn for btn in soup.find_all('button') if not btn.text.strip()]),
            "links_without_text": len([a for a in soup.find_all('a') if not a.text.strip() and not a.get('aria-label')]),
            "has_skip_link": bool(soup.find('a', string=re.compile(r'skip|main content', re.I))),
            "has_lang_attr": bool(soup.find('html', {'lang': True})),
            "tables": len(soup.find_all('table')),
            "videos": len(soup.find_all('video')) + len(soup.find_all('iframe', src=re.compile(r'youtube|vimeo')))
        }
        
        # Determine site type
        site_type = self._detect_site_type(url, html_content)
        
        # Create context-aware prompt for NVIDIA NIM
        prompt = f"""
        Analyze the accessibility of this {site_type} website and provide detailed, actionable feedback.
        
        URL: {url}
        
        Structural Analysis:
        - Images: {metrics['images_total']} total, {metrics['images_without_alt']} missing alt text
        - Forms: {metrics['forms']} forms found
        - Headings: {metrics['headings']['h1']} H1, {metrics['headings']['h2']} H2, {metrics['headings']['h3']} H3
        - ARIA landmarks: {metrics['aria_landmarks']}
        - Buttons without text: {metrics['buttons_without_text']}
        - Links without text: {metrics['links_without_text']}
        - Has skip navigation: {metrics['has_skip_link']}
        - Has language attribute: {metrics['has_lang_attr']}
        - Tables: {metrics['tables']}
        - Videos/Media: {metrics['videos']}
        
        For a {site_type} website, provide:
        
        1. ACCESSIBILITY SCORE (0-100):
        Consider:
        - For news/sports sites like ESPN: Well-structured content, proper headings, and navigation should score 75-85
        - For e-commerce: Focus on form accessibility, product descriptions
        - For developer sites: Code examples, documentation structure
        - Penalize heavily for: missing alt text, no skip links, poor heading structure
        - Reward for: ARIA landmarks, proper semantics, keyboard navigation
        
        2. TOP 5 ISSUES:
        For each issue provide:
        - Title (specific and actionable)
        - Severity (Critical/Major/Minor)
        - Description (what's wrong and where)
        - Impact (who it affects and how)
        - Specific fix with code example
        
        3. CONTEXTUAL RECOMMENDATIONS:
        Provide 3 specific recommendations for improving this {site_type} site's accessibility
        
        Return as JSON with structure:
        {{
            "score": <number>,
            "score_reasoning": "<detailed explanation>",
            "issues": [...],
            "recommendations": [...],
            "strengths": [...]
        }}
        """
        
        try:
            response = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={
                    "model": PRIMARY_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an expert accessibility auditor. Provide accurate, context-aware scores where well-structured sites score 70-90, average sites 50-70, and poor sites below 50."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                
                # Parse JSON response
                try:
                    # Extract JSON from potential markdown
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group(1))
                    else:
                        result = json.loads(content)
                    
                    # Ensure score is reasonable
                    score = result.get('score', 50)
                    if site_type in ['sports', 'news'] and metrics['has_skip_link'] and metrics['headings']['h1'] > 0:
                        score = max(score, 70)  # Well-structured sites shouldn't score too low
                    
                    result['score'] = min(100, max(0, score))
                    result['metrics'] = metrics
                    result['site_type'] = site_type
                    
                    return result
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from response: {content}")
                    return self._fallback_analysis(metrics, site_type)
            else:
                logger.error(f"NVIDIA API error: {response.status_code}")
                return self._fallback_analysis(metrics, site_type)
                
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return self._fallback_analysis(metrics, site_type)
    
    def _detect_site_type(self, url: str, content: str) -> str:
        """Detect the type of website"""
        url_lower = url.lower()
        content_lower = content.lower()
        
        if 'espn' in url_lower or 'sports' in content_lower[:1000]:
            return 'sports'
        elif 'news' in url_lower or 'article' in content_lower[:1000]:
            return 'news'
        elif 'shop' in url_lower or 'cart' in content_lower:
            return 'e-commerce'
        elif 'github' in url_lower or 'code' in content_lower[:500]:
            return 'developer'
        elif 'edu' in url_lower:
            return 'educational'
        else:
            return 'general'
    
    def _fallback_analysis(self, metrics: Dict, site_type: str) -> Dict:
        """Fallback analysis when API fails"""
        # Calculate score based on metrics
        score = 70  # Base score
        
        # Deductions
        if metrics['images_without_alt'] > 0:
            score -= min(20, metrics['images_without_alt'] * 2)
        if metrics['buttons_without_text'] > 0:
            score -= min(10, metrics['buttons_without_text'] * 3)
        if metrics['links_without_text'] > 0:
            score -= min(10, metrics['links_without_text'] * 2)
        if not metrics['has_skip_link']:
            score -= 10
        if not metrics['has_lang_attr']:
            score -= 5
        if metrics['headings']['h1'] == 0:
            score -= 15
        
        # Bonuses
        if metrics['aria_landmarks'] > 3:
            score += 10
        if metrics['has_skip_link']:
            score += 5
        
        # Adjust for site type
        if site_type in ['sports', 'news'] and metrics['headings']['h1'] > 0:
            score = max(score, 65)
        
        issues = []
        
        if metrics['images_without_alt'] > 0:
            issues.append({
                "title": f"{metrics['images_without_alt']} images missing alt text",
                "severity": "Critical",
                "description": "Images without alt text are invisible to screen readers",
                "impact": "Screen reader users cannot understand image content",
                "fix": '<img src="image.jpg" alt="Descriptive text about the image">'
            })
        
        if not metrics['has_skip_link']:
            issues.append({
                "title": "No skip navigation link",
                "severity": "Major",
                "description": "Users must tab through all navigation to reach main content",
                "impact": "Keyboard users waste time navigating repetitive content",
                "fix": '<a href="#main" class="skip-link">Skip to main content</a>'
            })
        
        if metrics['headings']['h1'] == 0:
            issues.append({
                "title": "Missing H1 heading",
                "severity": "Major",
                "description": "Page lacks a main H1 heading for structure",
                "impact": "Screen reader users cannot understand page hierarchy",
                "fix": '<h1>Main Page Title</h1>'
            })
        
        return {
            "score": max(0, min(100, score)),
            "score_reasoning": "Score calculated based on structural analysis and accessibility violations",
            "issues": issues[:5],
            "recommendations": [
                f"Add alt text to all {metrics['images_without_alt']} images",
                "Implement skip navigation links",
                "Ensure proper heading hierarchy"
            ],
            "strengths": [
                f"Has {metrics['aria_landmarks']} ARIA landmarks" if metrics['aria_landmarks'] > 0 else "Consider adding ARIA landmarks"
            ],
            "metrics": metrics,
            "site_type": site_type
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Global analyzer instance
analyzer = AccessibilityAnalyzer()

@app.post("/api/audit")
async def audit_website(
    url: str = Form(...),
    html_content: str = Form(...),
    screenshot: Optional[UploadFile] = File(None)
):
    """
    Main audit endpoint - analyzes website accessibility
    """
    try:
        # Process screenshot if provided
        screenshot_data = None
        if screenshot:
            screenshot_data = await screenshot.read()
        
        # Perform analysis
        result = await analyzer.analyze_with_context(
            url=url,
            html_content=html_content,
            screenshot=screenshot_data
        )
        
        # Log the audit
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "score": result.get("score", 0),
            "site_type": result.get("site_type", "unknown"),
            "issues_count": len(result.get("issues", [])),
            "has_screenshot": screenshot is not None
        }
        logger.info(f"Audit completed: {json.dumps(log_entry)}")
        
        # Format response for frontend
        formatted_issues = []
        for i, issue in enumerate(result.get("issues", []), 1):
            formatted_issues.append({
                "id": i,
                "title": issue.get("title", "Issue"),
                "severity": issue.get("severity", "Minor"),
                "description": issue.get("description", ""),
                "impact": issue.get("impact", ""),
                "element": issue.get("element", ""),
                "fix": issue.get("fix", ""),
                "wcag": issue.get("wcag", "")
            })
        
        response = {
            "score": result.get("score", 50),
            "grade": _score_to_grade(result.get("score", 50)),
            "summary": result.get("score_reasoning", "Accessibility analysis completed"),
            "issues": formatted_issues,
            "recommendations": result.get("recommendations", []),
            "strengths": result.get("strengths", []),
            "timestamp": datetime.now().isoformat(),
            "metrics": result.get("metrics", {}),
            "site_type": result.get("site_type", "general")
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Audit error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "model": PRIMARY_MODEL,
        "timestamp": datetime.now().isoformat()
    }

def _score_to_grade(score: float) -> str:
    """Convert score to letter grade"""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await analyzer.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)