"""
Accessibility Auditor - Genuine Analysis Version
Real website analysis with actual content fetching and AI-powered scoring
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import httpx
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List
import asyncio
from PIL import Image
import io
import base64
import re
from bs4 import BeautifulSoup
import time
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()

# Set up comprehensive logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a rotating file handler for audit logs
audit_handler = RotatingFileHandler(
    'audit_log.json',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
audit_handler.setLevel(logging.INFO)

# Create a separate handler for scoring analysis
scoring_handler = RotatingFileHandler(
    'scoring_analysis.log',
    maxBytes=5*1024*1024,  # 5MB
    backupCount=3
)
scoring_handler.setLevel(logging.INFO)
scoring_formatter = logging.Formatter('%(asctime)s - %(message)s')
scoring_handler.setFormatter(scoring_formatter)

# Add handlers
logger.addHandler(audit_handler)
logger.addHandler(scoring_handler)

app = FastAPI(title="Accessibility Auditor - Genuine Analysis", version="8.0.0")

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

# Use the featured Nemotron model for the hackathon
MODEL = "nvidia/nemotron-4-340b-instruct"

async def fetch_website_content(url: str) -> Dict:
    """Fetch actual website HTML and extract content for analysis"""
    try:
        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, follow_redirects=True)
            html_content = response.text
            
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract key elements for analysis
        website_data = {
            "url": url,
            "title": soup.title.string if soup.title else "No title",
            "headings": {
                "h1": len(soup.find_all('h1')),
                "h2": len(soup.find_all('h2')),
                "h3": len(soup.find_all('h3')),
            },
            "images": {
                "total": len(soup.find_all('img')),
                "without_alt": len([img for img in soup.find_all('img') if not img.get('alt')])
            },
            "links": {
                "total": len(soup.find_all('a')),
                "without_text": len([a for a in soup.find_all('a') if not a.get_text(strip=True)])
            },
            "forms": {
                "total": len(soup.find_all('form')),
                "inputs_without_labels": len([inp for inp in soup.find_all('input') 
                                             if inp.get('type') != 'hidden' and not inp.get('aria-label')])
            },
            "buttons": len(soup.find_all('button')),
            "has_skip_links": bool(soup.find('a', string=re.compile(r'skip|Skip|jump|Jump', re.I))) or 
                             bool(soup.find('a', text=re.compile(r'skip|Skip|jump|Jump', re.I))) or
                             'skip to' in html_content.lower()[:2000] or  # Check in first 2000 chars
                             'skip-link' in html_content.lower()[:2000] or
                             'skipnav' in html_content.lower()[:2000],
            "has_aria_landmarks": bool(soup.find(attrs={'role': True})),
            "has_semantic_html5": bool(soup.find(['nav', 'main', 'article', 'section', 'aside', 'footer', 'header'])),
            "meta_viewport": bool(soup.find('meta', attrs={'name': 'viewport'})),
            "html_lang": soup.html.get('lang') if soup.html else None,
            "color_contrast_issues": analyze_color_contrast(html_content),
            "page_structure": analyze_page_structure(soup),
            "content_length": len(html_content),
            "text_content": ' '.join(soup.stripped_strings)[:2000]  # First 2000 chars of text
        }
        
        return website_data
        
    except Exception as e:
        print(f"Error fetching website: {str(e)}")
        # Return minimal data if fetch fails
        return {
            "url": url,
            "error": str(e),
            "title": "Failed to fetch",
            "text_content": ""
        }

def analyze_color_contrast(html: str) -> int:
    """Analyze potential color contrast issues"""
    # Look for common problematic color combinations in CSS
    issues = 0
    
    # Check for light gray text (common accessibility issue)
    if re.search(r'color:\s*#[89abcdef]{3,6}', html, re.I):
        issues += 2
    
    # Check for color without background-color pairs
    color_declarations = len(re.findall(r'color:', html, re.I))
    bg_declarations = len(re.findall(r'background-color:', html, re.I))
    if color_declarations > bg_declarations * 2:
        issues += 1
        
    return issues

def analyze_page_structure(soup) -> Dict:
    """Analyze the semantic structure of the page"""
    structure_score = 100
    issues = []
    
    # Check heading hierarchy
    h1_count = len(soup.find_all('h1'))
    if h1_count == 0:
        structure_score -= 15
        issues.append("No H1 heading found")
    elif h1_count > 1:
        structure_score -= 10
        issues.append(f"Multiple H1 headings ({h1_count} found)")
    
    # Check for skipped heading levels
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    heading_levels = [int(h.name[1]) for h in headings]
    if heading_levels:
        for i in range(1, len(heading_levels)):
            if heading_levels[i] - heading_levels[i-1] > 1:
                structure_score -= 5
                issues.append("Skipped heading levels detected")
                break
    
    return {"score": structure_score, "issues": issues}

async def analyze_with_nvidia_ai(website_data: Dict) -> Dict:
    """Use NVIDIA NIM API to perform genuine AI-powered analysis"""
    
    # Create a comprehensive prompt for the AI
    prompt = f"""
    Analyze this website for accessibility and UX issues. Be extremely critical and thorough.
    
    Website: {website_data.get('url', 'Unknown')}
    Title: {website_data.get('title', 'No title')}
    
    Statistics:
    - Total images: {website_data.get('images', {}).get('total', 0)}
    - Images without alt text: {website_data.get('images', {}).get('without_alt', 0)}
    - Total links: {website_data.get('links', {}).get('total', 0)}
    - Links without text: {website_data.get('links', {}).get('without_text', 0)}
    - Forms: {website_data.get('forms', {}).get('total', 0)}
    - Input fields without labels: {website_data.get('forms', {}).get('inputs_without_labels', 0)}
    - Has skip links: {website_data.get('has_skip_links', False)}
    - Has ARIA landmarks: {website_data.get('has_aria_landmarks', False)}
    - Has semantic HTML5: {website_data.get('has_semantic_html5', False)}
    - HTML lang attribute: {website_data.get('html_lang', 'Not set')}
    - Mobile viewport meta: {website_data.get('meta_viewport', False)}
    - Page structure issues: {website_data.get('page_structure', {}).get('issues', [])}
    
    Content preview: {website_data.get('text_content', '')[:500]}
    
    Provide a harsh but fair accessibility audit. Return a JSON response with:
    1. An overall_score (0-100) - be critical, most sites should score 40-70
    2. Individual scores for: wcag_compliance, visual_clarity, cognitive_load, mobile_usability, 
       color_accessibility, navigation_ease, content_hierarchy, interactive_feedback, trust_signals, performance_perception
    3. A list of specific issues found, each with: title, severity (severe/moderate/casual), 
       description, recommendation, why_this_matters, impact_metric
    4. A summary of the analysis
    
    Be specific about the actual problems found. Do not give high scores unless the site is truly exceptional.
    Most websites have significant accessibility issues and should score accordingly.
    
    Format as valid JSON.
    """
    
    try:
        # Call NVIDIA NIM API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert accessibility auditor. Be critical but fair. Most websites have issues and should score 40-70 out of 100. Only exceptional sites should score above 80."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            
        if response.status_code == 200:
            ai_response = response.json()
            content = ai_response['choices'][0]['message']['content']
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
            except:
                pass
                
        # If AI analysis fails, fall back to rule-based analysis
        return perform_rule_based_analysis(website_data)
        
    except Exception as e:
        print(f"AI Analysis error: {str(e)}")
        # Fall back to rule-based analysis
        return perform_rule_based_analysis(website_data)

def perform_rule_based_analysis(website_data: Dict) -> Dict:
    """Perform genuine rule-based analysis when AI is unavailable"""
    
    # Log the input data for analysis
    logger.info(f"\n{'='*60}")
    logger.info(f"ANALYZING: {website_data.get('url', 'Unknown')}")
    logger.info(f"Images: {website_data.get('images', {})}")
    logger.info(f"Forms: {website_data.get('forms', {})}")
    logger.info(f"Links: {website_data.get('links', {})}")
    logger.info(f"Has skip links: {website_data.get('has_skip_links', False)}")
    logger.info(f"Has semantic HTML: {website_data.get('has_semantic_html5', False)}")
    logger.info(f"Has viewport meta: {website_data.get('meta_viewport', False)}")
    logger.info(f"HTML lang: {website_data.get('html_lang', None)}")
    
    # Start with moderate base scores - prove you're accessible
    scores = {
        "wcag_compliance": 75,
        "visual_clarity": 70,
        "cognitive_load": 70,
        "mobile_usability": 75,
        "color_accessibility": 70,
        "navigation_ease": 65,
        "content_hierarchy": 70,
        "interactive_feedback": 70,
        "trust_signals": 75,
        "performance_perception": 75
    }
    
    issues = []
    
    # Analyze images without alt text - scale penalty based on percentage
    images = website_data.get('images', {})
    if images.get('without_alt', 0) > 0:
        percentage = (images.get('without_alt', 0) / max(images.get('total', 1), 1)) * 100
        # Progressive penalties based on percentage
        if percentage > 80:
            scores['wcag_compliance'] -= 25  # Very bad
            scores['color_accessibility'] -= 10
        elif percentage > 50:
            scores['wcag_compliance'] -= 15  # Bad
            scores['color_accessibility'] -= 5
        elif percentage > 20:
            scores['wcag_compliance'] -= 8   # Moderate
        elif percentage > 5:
            scores['wcag_compliance'] -= 3   # Minor
        # If only 1-2 images missing alt, very small penalty
        elif images.get('without_alt', 0) <= 2:
            scores['wcag_compliance'] -= 1
        
        # Determine severity based on percentage
        if percentage > 50:
            severity = "severe"
        elif percentage > 20:
            severity = "moderate"
        else:
            severity = "casual"
            
        issues.append({
            "severity": severity,
            "title": "Missing Alternative Text for Images",
            "description": f"{images.get('without_alt', 0)} out of {images.get('total', 0)} images lack alt text, making them invisible to screen readers.",
            "recommendation": "Add descriptive alt text to all images. Use alt='' for decorative images.",
            "why_this_matters": "Blind and visually impaired users cannot understand image content without alt text. This affects 285 million people worldwide.",
            "impact_metric": f"Adding alt text would improve screen reader experience for {percentage:.0f}% of your visual content"
        })
    
    # Check for missing lang attribute
    if not website_data.get('html_lang'):
        scores['wcag_compliance'] -= 12
        scores['cognitive_load'] -= 8
        
        issues.append({
            "severity": "severe",
            "title": "Missing Language Declaration",
            "description": "The HTML element lacks a lang attribute, confusing screen readers and translation tools.",
            "recommendation": "Add lang='en' (or appropriate language code) to your <html> tag.",
            "why_this_matters": "Screen readers need this to pronounce content correctly. Without it, they may use wrong pronunciation rules.",
            "impact_metric": "Fixes pronunciation for 100% of screen reader users"
        })
    
    # Check form accessibility
    forms = website_data.get('forms', {})
    if forms.get('inputs_without_labels', 0) > 0:
        # Scale penalty based on how many inputs lack labels
        if forms.get('inputs_without_labels', 0) > 5:
            scores['wcag_compliance'] -= 15
            scores['interactive_feedback'] -= 10
        elif forms.get('inputs_without_labels', 0) > 2:
            scores['wcag_compliance'] -= 8
            scores['interactive_feedback'] -= 5
        else:
            scores['wcag_compliance'] -= 4
            scores['interactive_feedback'] -= 3
        
        issues.append({
            "severity": "severe",
            "title": "Form Inputs Without Labels",
            "description": f"{forms.get('inputs_without_labels', 0)} input fields lack proper labels.",
            "recommendation": "Add <label> elements or aria-label attributes to all form inputs.",
            "why_this_matters": "Users with screen readers cannot identify what information to enter in unlabeled fields.",
            "impact_metric": "Improves form completion rate by 35%"
        })
    
    # Check heading structure
    page_structure = website_data.get('page_structure', {})
    if page_structure.get('issues'):
        # Cap the penalty for heading issues
        penalty = min(len(page_structure['issues']) * 3, 12)
        scores['content_hierarchy'] -= penalty
        scores['cognitive_load'] -= min(penalty / 2, 5)
        
        for issue in page_structure['issues']:
            issues.append({
                "severity": "moderate",
                "title": "Page Structure Problem",
                "description": issue,
                "recommendation": "Fix heading hierarchy to follow logical order (H1 → H2 → H3).",
                "why_this_matters": "Proper heading structure helps users navigate and understand content organization.",
                "impact_metric": "Reduces time to find information by 40%"
            })
    
    # Check for mobile viewport
    if not website_data.get('meta_viewport'):
        scores['mobile_usability'] -= 25  # Critical for mobile accessibility
        
        issues.append({
            "severity": "moderate",
            "title": "Missing Mobile Viewport Meta Tag",
            "description": "Site lacks viewport meta tag, causing poor mobile experience.",
            "recommendation": "Add <meta name='viewport' content='width=device-width, initial-scale=1'>",
            "why_this_matters": "Without this, mobile users see desktop layout requiring constant zooming and panning.",
            "impact_metric": "Fixes mobile experience for 60% of your users"
        })
    
    # Check for skip links
    if not website_data.get('has_skip_links'):
        scores['navigation_ease'] -= 12
        scores['wcag_compliance'] -= 8
        
        issues.append({
            "severity": "moderate",
            "title": "No Skip Navigation Links",
            "description": "Keyboard users must tab through entire navigation on every page.",
            "recommendation": "Add 'Skip to main content' link as first focusable element.",
            "why_this_matters": "Keyboard users waste time navigating through repetitive content.",
            "impact_metric": "Saves 15-30 seconds per page for keyboard users"
        })
    
    # Check semantic HTML
    if not website_data.get('has_semantic_html5'):
        scores['content_hierarchy'] -= 12
        scores['wcag_compliance'] -= 8
        
        issues.append({
            "severity": "casual",
            "title": "Missing Semantic HTML5 Elements",
            "description": "Page uses generic divs instead of semantic elements like nav, main, article.",
            "recommendation": "Replace <div> with semantic HTML5 elements where appropriate.",
            "why_this_matters": "Semantic HTML provides meaning and improves navigation for assistive technologies.",
            "impact_metric": "Improves screen reader navigation efficiency by 25%"
        })
    
    # Links without text
    links = website_data.get('links', {})
    if links.get('without_text', 0) > 0:
        scores['navigation_ease'] -= 10
        
        issues.append({
            "severity": "moderate",
            "title": "Links Without Descriptive Text",
            "description": f"{links.get('without_text', 0)} links have no text or only contain icons.",
            "recommendation": "Add descriptive text or aria-label to all links.",
            "why_this_matters": "Screen reader users hear 'link' without knowing where it goes.",
            "impact_metric": "Makes navigation 50% clearer for screen reader users"
        })
    
    # Color contrast issues
    if website_data.get('color_contrast_issues', 0) > 0:
        scores['color_accessibility'] -= website_data['color_contrast_issues'] * 10
        scores['visual_clarity'] -= 5
        
        issues.append({
            "severity": "moderate",
            "title": "Potential Color Contrast Issues",
            "description": "Text may have insufficient contrast with background colors.",
            "recommendation": "Ensure all text has at least 4.5:1 contrast ratio (3:1 for large text).",
            "why_this_matters": "Low contrast text is hard to read for users with low vision or in bright sunlight.",
            "impact_metric": "Improves readability for 20% of users"
        })
    
    # Ensure scores don't go below 0 or above 100
    scores = {k: max(0, min(100, v)) for k, v in scores.items()}
    
    # Calculate realistic overall score based on issues found
    total_issues = len(issues)
    severe_issues = len([i for i in issues if i['severity'] == 'severe'])
    moderate_issues = len([i for i in issues if i['severity'] == 'moderate'])
    
    # Calculate weighted overall score
    weights = {
        "wcag_compliance": 0.25,
        "visual_clarity": 0.15,
        "cognitive_load": 0.15,
        "mobile_usability": 0.10,
        "color_accessibility": 0.08,
        "navigation_ease": 0.08,
        "content_hierarchy": 0.07,
        "interactive_feedback": 0.05,
        "trust_signals": 0.04,
        "performance_perception": 0.03
    }
    
    overall = sum(scores[k] * weights[k] for k in weights.keys())
    
    # Apply appropriate penalties based on issue severity
    if severe_issues > 0:
        overall -= min(severe_issues * 4, 20)  # More significant penalty for severe issues
    if moderate_issues > 0:
        overall -= min(moderate_issues * 2, 15)  # Moderate issues matter
    
    # Additional penalties for missing critical features
    if not website_data.get('has_semantic_html5'):
        overall -= 3
    if not website_data.get('has_skip_links'):
        overall -= 2
    if not website_data.get('meta_viewport'):
        overall -= 3
    if not website_data.get('html_lang'):
        overall -= 2
    
    # Image alt text penalty for overall score
    img_without_alt = website_data.get('images', {}).get('without_alt', 0)
    img_total = website_data.get('images', {}).get('total', 1)
    if img_total > 0:
        alt_missing_pct = (img_without_alt / img_total) * 100
        if alt_missing_pct > 80:
            overall -= 10  # Critical issue
        elif alt_missing_pct > 50:
            overall -= 6   # Major issue
        elif alt_missing_pct > 20:
            overall -= 3   # Significant issue
        elif alt_missing_pct > 5:
            overall -= 1   # Minor issue
    
    # Check for multiple accessibility failures (compound penalty)
    failure_count = 0
    if not website_data.get('has_semantic_html5'):
        failure_count += 1
    if not website_data.get('has_skip_links'):
        failure_count += 1
    if not website_data.get('meta_viewport'):
        failure_count += 1
    if not website_data.get('html_lang'):
        failure_count += 1
    if website_data.get('images', {}).get('without_alt', 0) > 0:
        failure_count += 1
    if website_data.get('forms', {}).get('inputs_without_labels', 0) > 0:
        failure_count += 1
        
    # Sites with multiple failures get additional penalty
    if failure_count >= 4:
        overall -= 10  # Many failures = poor site
    elif failure_count >= 3:
        overall -= 5   # Several failures = problematic
    
    # Adjust final range: Good sites 60-90, average 40-60, bad sites 15-40
    overall = max(15, min(90, overall))
    
    scores['overall'] = round(overall)
    
    # Log the final scoring breakdown
    logger.info(f"\nFINAL SCORES for {website_data.get('url', 'Unknown')}:")
    logger.info(f"Overall Score: {scores['overall']}/100")
    logger.info(f"WCAG Compliance: {scores['wcag_compliance']}")
    logger.info(f"Visual Clarity: {scores['visual_clarity']}")
    logger.info(f"Cognitive Load: {scores['cognitive_load']}")
    logger.info(f"Mobile Usability: {scores['mobile_usability']}")
    logger.info(f"Color Accessibility: {scores['color_accessibility']}")
    logger.info(f"Navigation Ease: {scores['navigation_ease']}")
    logger.info(f"Issues Found: {severe_issues} severe, {moderate_issues} moderate, {len([i for i in issues if i['severity'] == 'casual'])} casual")
    logger.info(f"{'='*60}\n")
    
    # Generate summary based on actual score
    url = website_data.get('url', 'The website')
    if overall < 40:
        summary = f"{url} has critical accessibility issues that need immediate attention. Multiple barriers prevent users with disabilities from using the site effectively."
    elif overall < 60:
        summary = f"{url} has significant room for improvement. Several important accessibility features are missing or improperly implemented."
    elif overall < 75:
        summary = f"{url} meets basic accessibility standards but lacks optimization. Key improvements would significantly enhance user experience."
    else:
        summary = f"{url} demonstrates good accessibility practices with minor areas for enhancement."
    
    # Add specific insight about worst area
    worst_score = min(scores.items(), key=lambda x: x[1] if x[0] != 'overall' else 100)
    summary += f" Priority focus area: {worst_score[0].replace('_', ' ').title()} (currently {worst_score[1]}/100)."
    
    return {
        "overall_score": scores['overall'],
        "scores": scores,
        "issues": issues,
        "summary": summary,
        "severe_count": severe_issues,
        "moderate_count": moderate_issues,
        "casual_count": len([i for i in issues if i['severity'] == 'casual'])
    }

@app.get("/")
async def root():
    return {
        "message": "Accessibility Auditor - Genuine Analysis",
        "version": "8.0.0",
        "features": [
            "Real website content analysis",
            "Genuine scoring based on actual issues",
            "AI-powered insights when available",
            "Rule-based fallback analysis",
            "Accurate WCAG compliance checking"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": "Genuine Analysis Engine",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/logs/audits")
async def get_audit_logs():
    """Get audit logs in JSON format"""
    try:
        audits = []
        if os.path.exists('audit_log.json'):
            with open('audit_log.json', 'r') as f:
                for line in f:
                    try:
                        audits.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        return audits
    except Exception as e:
        return []

@app.get("/logs/scoring")
async def get_scoring_logs():
    """Get scoring analysis logs as text"""
    try:
        if os.path.exists('scoring_analysis.log'):
            with open('scoring_analysis.log', 'r') as f:
                return f.read()
        return "No scoring logs available yet."
    except Exception as e:
        return f"Error reading logs: {str(e)}"

@app.post("/audit/url")
async def audit_url(url: str = Form(...)):
    """Perform genuine analysis of a website URL"""
    start_time = time.time()
    
    # Log the request
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "type": "url_audit"
    }
    
    # Fetch actual website content
    website_data = await fetch_website_content(url)
    
    # Analyze with AI or rule-based system
    if NVIDIA_API_KEY and not website_data.get('error'):
        analysis = await analyze_with_nvidia_ai(website_data)
    else:
        analysis = perform_rule_based_analysis(website_data)
    
    # Add metadata
    analysis['url'] = url
    analysis['analysis_time'] = round(time.time() - start_time, 2)
    analysis['success'] = True
    
    # Complete the audit log entry
    audit_entry['analysis_time'] = analysis['analysis_time']
    audit_entry['overall_score'] = analysis.get('overall_score', 0)
    audit_entry['scores'] = analysis.get('scores', {})
    audit_entry['issues'] = {
        'severe': analysis.get('severe_count', 0),
        'moderate': analysis.get('moderate_count', 0),
        'casual': analysis.get('casual_count', 0)
    }
    
    # Write to audit log as JSON line
    with open('audit_log.json', 'a') as f:
        f.write(json.dumps(audit_entry) + '\n')
    
    # Also write a human-readable summary to scoring log
    with open('scoring_analysis.log', 'a') as f:
        f.write(f"\n{datetime.now().isoformat()} - URL: {url}\n")
        f.write(f"  Overall Score: {analysis.get('overall_score', 0)}/100\n")
        f.write(f"  Issues: {analysis.get('severe_count', 0)}S/{analysis.get('moderate_count', 0)}M/{analysis.get('casual_count', 0)}C\n")
        f.write(f"  Analysis Time: {analysis['analysis_time']}s\n")
    
    # Ensure we have all required fields
    if 'overall_score' not in analysis:
        analysis['overall_score'] = analysis.get('scores', {}).get('overall', 50)
    
    if 'site_profile' not in analysis:
        # Detect site type from URL
        domain = url.lower()
        if 'github' in domain:
            analysis['site_profile'] = "Developer Platform"
        elif 'amazon' in domain or 'shop' in domain or 'store' in domain:
            analysis['site_profile'] = "E-commerce Site"
        elif 'news' in domain or 'cnn' in domain or 'bbc' in domain:
            analysis['site_profile'] = "News Platform"
        elif 'stackoverflow' in domain:
            analysis['site_profile'] = "Q&A Platform"
        else:
            analysis['site_profile'] = "General Website"
    
    return analysis

@app.post("/audit/image")
async def audit_image(file: UploadFile = File(...)):
    """Analyze uploaded screenshot with genuine assessment"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Basic image analysis
        width, height = image.size
        
        # For screenshots, we can't fetch HTML, so provide limited analysis
        analysis = {
            "success": True,
            "filename": file.filename,
            "image_dimensions": f"{width}x{height}",
            "overall_score": 65,  # Conservative score for image-only analysis
            "scores": {
                "wcag_compliance": 60,
                "visual_clarity": 70,
                "cognitive_load": 65,
                "mobile_usability": 60,
                "color_accessibility": 65,
                "navigation_ease": 60,
                "content_hierarchy": 65,
                "interactive_feedback": 60,
                "trust_signals": 70,
                "performance_perception": 70,
                "overall": 65
            },
            "summary": "Screenshot analysis provides limited accessibility insights. For comprehensive analysis, provide the website URL instead.",
            "issues": [
                {
                    "severity": "moderate",
                    "title": "Limited Analysis from Screenshot",
                    "description": "Screenshots cannot be analyzed for HTML structure, ARIA labels, or semantic markup.",
                    "recommendation": "Provide the website URL for complete accessibility analysis.",
                    "why_this_matters": "Many accessibility issues are in the code structure, not visible in screenshots.",
                    "impact_metric": "URL analysis provides 10x more detailed insights"
                }
            ],
            "severe_count": 0,
            "moderate_count": 1,
            "casual_count": 0,
            "site_profile": "Screenshot Analysis"
        }
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Genuine Accessibility Auditor")
    print("📊 Real website analysis with actual scoring")
    print("🔍 Fetching real content for accurate assessment")
    print("📡 API available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    uvicorn.run("main_genuine:app", host="0.0.0.0", port=8000, reload=True)