"""
Professional Web Accessibility Auditor - NVIDIA NIM Multi-Model Architecture
Models: Llama 3.1 70B (analysis), Nemotron Nano VL 8B (vision), Nemotron Nano 9B (chat)
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Literal
from datetime import datetime
from dotenv import load_dotenv
import os
import json
import httpx
from PIL import Image
import io
import base64
import re
from bs4 import BeautifulSoup
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Professional Accessibility Auditor API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIG
# ============================================================================
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

MODEL_LLM = "meta/llama-3.1-70b-instruct"  # Main analysis
MODEL_VISION = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"  # Screenshots
MODEL_CHAT = "nvidia/nvidia-nemotron-nano-9b-v2"  # Follow-up Q&A

# ============================================================================
# DATA MODELS
# ============================================================================
class AccessibilityIssue(BaseModel):
    title: str
    severity: Literal["Critical", "Major", "Minor"]
    categories: List[str]  # WCAG, Psychological, Performance, SEO, General
    description: str
    impact: str
    solution: str  # Natural language, actionable
    wcag_reference: Optional[str] = None

class ChatMessage(BaseModel):
    message: str
    context: Optional[Dict] = None  # Audit report for context

# ============================================================================
# KNOWLEDGE BASE
# ============================================================================
WCAG_KNOWLEDGE = """
WCAG 2.1 AA Critical Guidelines:
- 1.1.1: Text alternatives for images
- 1.3.1: Info/relationships programmatically determinable
- 1.4.3: Contrast minimum 4.5:1
- 2.1.1: Keyboard accessible
- 2.4.1: Bypass blocks (skip links)
- 3.1.1: Language of page
- 4.1.2: Name, role, value for components
"""

PSYCHOLOGY_KNOWLEDGE = """
Web Psychology Principles:
- Cognitive Load: 7±2 items max (Miller's Law)
- Fitts' Law: Larger targets = easier interaction
- Hick's Law: More choices = slower decisions
- F-Pattern: Users scan F-shaped
- Gestalt: Proximity, similarity, continuity
- Visual Hierarchy: Size/color guide attention
"""

BEST_PRACTICES = """
Modern Web Standards:
- Mobile-first design
- Core Web Vitals: LCP<2.5s, FID<100ms, CLS<0.1
- 16px min font, 1.5 line-height
- 45-75 chars per line
- Progressive enhancement
"""

# ============================================================================
# NVIDIA NIM CLIENT
# ============================================================================
class NVIDIAClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def chat(self, model: str, messages: List[Dict], temp: float = 0.1, max_tok: int = 4000, top_p: float = 0.7) -> Dict:
        """Call NVIDIA chat completion"""
        try:
            resp = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temp,
                    "top_p": top_p,
                    "max_tokens": max_tok
                }
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"API Response: {data}")
            return data
        except Exception as e:
            logger.error(f"NVIDIA API error: {e}")
            raise HTTPException(502, f"API error: {e}")

    async def vision(self, image_bytes: bytes, prompt: str) -> Dict:
        """Call NVIDIA vision model"""
        try:
            img_b64 = base64.b64encode(image_bytes).decode('utf-8')
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }]
            resp = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={"model": MODEL_VISION, "messages": messages, "temperature": 0.2, "max_tokens": 2000}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            raise HTTPException(500, f"Vision failed: {e}")

    async def vision_multi(self, images_bytes: List[bytes], prompt: str) -> Dict:
        """Call NVIDIA vision model with multiple images in shared context"""
        try:
            content = [{"type": "text", "text": prompt}]
            for idx, img_bytes in enumerate(images_bytes):
                img_b64 = base64.b64encode(img_bytes).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                })

            messages = [{"role": "user", "content": content}]
            resp = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={"model": MODEL_VISION, "messages": messages, "temperature": 0.2, "max_tokens": 3000}
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Multi-vision API error: {e}")
            raise HTTPException(500, f"Multi-vision failed: {e}")

    async def close(self):
        await self.client.aclose()

nim = NVIDIAClient()

# ============================================================================
# ANALYZER
# ============================================================================
class Analyzer:
    async def analyze_html(self, url: str, html: str) -> Dict:
        """Analyze HTML structure"""
        soup = BeautifulSoup(html, 'html.parser')
        metrics = self._get_metrics(soup)

        # Extract visible text and structure for context
        page_title = soup.find('title')
        page_title_text = page_title.get_text() if page_title else "No title"

        system = f"""You are a professional web design and accessibility auditor. Analyze websites across 5 categories: WCAG Accessibility, UX Psychology, Visual Design, SEO, and Performance.

Use this knowledge base:
{WCAG_KNOWLEDGE}
{PSYCHOLOGY_KNOWLEDGE}
{BEST_PRACTICES}

CRITICAL: You MUST return ONLY valid JSON. No markdown, no explanations, ONLY the JSON object."""

        user = f"""Analyze {url} (Title: "{page_title_text}")

HTML Metrics:
{json.dumps(metrics, indent=2)}

Provide a REAL analysis based on these ACTUAL metrics. Find SPECIFIC issues from the data above.

Return ONLY this JSON structure (no markdown, no code blocks):
{{
  "score": <number 0-100 based on issues found>,
  "summary": "Brief 1-sentence overview of main findings",
  "issues": [
    {{
      "title": "Specific issue title",
      "severity": "Critical|Major|Minor",
      "categories": ["WCAG Accessibility|Psychological/UX|Performance|SEO/Discoverability|General Improvement"],
      "description": "What is wrong and where",
      "impact": "Who is affected and how",
      "solution": "Actionable recommendation in natural language",
      "wcag_reference": "WCAG reference if applicable or null"
    }}
  ]
}}

IMPORTANT:
1. Base issues on ACTUAL metrics provided (e.g., if images_without_alt = 5, mention that specific number)
2. Calculate score honestly: 90-100 = excellent, 70-89 = good, 50-69 = needs work, 0-49 = poor
3. Score should decrease significantly for Critical issues
4. Order issues by severity (Critical > Major > Minor)
5. Provide natural language solutions, not code
6. Return 3-8 real issues based on what you find in the metrics
7. Return ONLY JSON, no other text or markdown"""

        resp = await nim.chat(MODEL_LLM, [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ], temp=0.1, top_p=0.7)

        content = resp['choices'][0]['message']['content']
        logger.info(f"LLM Response: {content[:500]}...")
        result = self._parse_json(content)
        result['metrics'] = metrics
        result['analysis_type'] = 'html'
        return result

    async def analyze_vision(self, img_bytes: bytes, url: Optional[str] = None) -> Dict:
        """Analyze screenshot"""
        prompt = f"""You are a professional web design auditor. Analyze this screenshot for visual accessibility and UX issues.

Examine WHAT YOU ACTUALLY SEE:
1. Color contrast between text and backgrounds (WCAG requires 4.5:1 for normal text, 3:1 for large text)
2. Text size and readability
3. Visual hierarchy - how elements guide the eye
4. Cognitive load - information density and whitespace
5. Touch target sizes (minimum 44x44px for mobile)
6. Design consistency and patterns

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "score": <number 0-100 based on what you observe>,
  "summary": "Brief description of what you see",
  "issues": [
    {{
      "title": "Specific visual issue you observe",
      "severity": "Critical|Major|Minor",
      "categories": ["WCAG Accessibility|Psychological/UX|Visual Design|General Improvement"],
      "description": "Describe the specific visual problem",
      "impact": "Who is affected and how",
      "solution": "Natural language recommendation",
      "wcag_reference": "WCAG reference if applicable or null"
    }}
  ]
}}

Score honestly based on severity: 90-100=excellent, 70-89=good, 50-69=needs work, 0-49=poor. Return 3-8 specific issues you observe."""

        resp = await nim.vision(img_bytes, prompt)
        content = resp['choices'][0]['message']['content']
        logger.info(f"Vision Response: {content[:500]}...")
        result = self._parse_json(content)
        result['analysis_type'] = 'vision'
        result['metrics'] = {}
        return result

    async def analyze_vision_multi(self, images_bytes: List[bytes], url: Optional[str] = None) -> Dict:
        """Analyze multiple screenshots with shared context"""
        prompt = f"""You are a professional web design auditor. Analyze these {len(images_bytes)} screenshots from the same website.

These images show different pages/views from ONE website. Analyze:
1. Color contrast across all pages (WCAG 4.5:1 for text, 3:1 for large text)
2. Text size and readability consistency
3. Visual hierarchy and information architecture
4. Cognitive load and whitespace usage
5. Cross-page design consistency and patterns
6. Touch target sizes (44x44px minimum)

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "score": <number 0-100 based on overall quality>,
  "summary": "Brief overview of what you observe across all screenshots",
  "issues": [
    {{
      "title": "Specific issue you observe",
      "severity": "Critical|Major|Minor",
      "categories": ["WCAG Accessibility|Psychological/UX|Visual Design|General Improvement"],
      "description": "What is wrong and which screenshot(s)",
      "impact": "Who is affected and how",
      "solution": "Natural language recommendation",
      "wcag_reference": "WCAG reference if applicable or null"
    }}
  ]
}}

Score honestly: 90-100=excellent, 70-89=good, 50-69=needs work, 0-49=poor. Return 3-8 specific issues across all screenshots."""

        resp = await nim.vision_multi(images_bytes, prompt)
        content = resp['choices'][0]['message']['content']
        logger.info(f"Multi-vision Response: {content[:500]}...")
        result = self._parse_json(content)
        result['analysis_type'] = 'vision_multi'
        result['metrics'] = {}
        return result

    async def combine(self, html_res: Dict, vision_res: Dict) -> Dict:
        """Merge HTML + vision analyses with dynamic category scoring"""
        issues = html_res.get('issues', []) + vision_res.get('issues', [])

        # Category-based dynamic scoring
        category_scores = self._calculate_category_scores(html_res, vision_res, has_html=True, has_vision=True)

        # Weighted final score: WCAG 30%, UX 30%, Design 25%, SEO 10%, Perf 5%
        score = int(
            category_scores['wcag'] * 0.30 +
            category_scores['ux_psychology'] * 0.30 +
            category_scores['visual_design'] * 0.25 +
            category_scores['seo'] * 0.10 +
            category_scores['performance'] * 0.05
        )

        return {
            'score': score,
            'category_scores': category_scores,
            'summary': f"Combined analysis: {len(issues)} issues found",
            'issues': issues,
            'metrics': html_res.get('metrics', {}),
            'analysis_type': 'combined'
        }

    def _calculate_category_scores(self, html_res: Optional[Dict], vision_res: Optional[Dict],
                                   has_html: bool, has_vision: bool) -> Dict[str, int]:
        """Calculate category scores based on input type"""
        # Get base scores from results
        html_score = html_res.get('score', 0) if html_res else 0
        vision_score = vision_res.get('score', 0) if vision_res else 0

        if has_html and has_vision:
            # Full analysis with both inputs
            return {
                'wcag': int(html_score * 0.70 + vision_score * 0.30),  # HTML primary
                'ux_psychology': int(vision_score * 0.70 + html_score * 0.30),  # Vision primary
                'visual_design': int(vision_score * 0.80 + html_score * 0.20),  # Vision dominant
                'seo': html_score,  # HTML only
                'performance': html_score  # HTML only
            }
        elif has_vision:
            # Vision-only: redistribute weights, exclude SEO/Performance
            return {
                'wcag': int(vision_score * 0.35),
                'ux_psychology': int(vision_score * 0.35),
                'visual_design': int(vision_score * 0.30),
                'seo': 0,  # Unavailable
                'performance': 0  # Unavailable
            }
        else:  # has_html
            # HTML-only: strong WCAG/SEO, limited visual
            return {
                'wcag': int(html_score * 0.40),
                'ux_psychology': int(html_score * 0.25),
                'visual_design': int(html_score * 0.10),
                'seo': int(html_score * 0.15),
                'performance': int(html_score * 0.10)
            }

    def _get_metrics(self, soup: BeautifulSoup) -> Dict:
        """Extract HTML metrics"""
        return {
            'images_total': len(soup.find_all('img')),
            'images_without_alt': len([i for i in soup.find_all('img') if not i.get('alt')]),
            'forms_count': len(soup.find_all('form')),
            'headings': {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1,7)},
            'aria_landmarks': len(soup.find_all(attrs={"role": True})),
            'buttons_without_text': len([b for b in soup.find_all('button') if not b.text.strip()]),
            'links_without_text': len([a for a in soup.find_all('a') if not a.text.strip() and not a.get('aria-label')]),
            'has_skip_link': bool(soup.find('a', string=re.compile(r'skip|main', re.I))),
            'has_lang_attr': bool(soup.find('html', {'lang': True})),
            'tables_count': len(soup.find_all('table')),
        }

    def _parse_json(self, content: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            return json.loads(content)
        except:
            # Try markdown block
            match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Try find JSON object
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError("No JSON found in response")

    def generate_who_helps(self, issues: List[Dict]) -> Dict[str, str]:
        """Generate real-world impact insights"""
        cats = {}
        for iss in issues:
            for cat in iss.get('categories', []):
                cats.setdefault(cat, []).append(iss)

        insights = {}

        if 'WCAG Accessibility' in cats:
            crit = len([i for i in cats['WCAG Accessibility'] if i['severity'] == 'Critical'])
            insights['People with Disabilities'] = (
                f"{crit} critical barriers affect screen reader users (15% of web), "
                f"keyboard navigators, and colorblind users (8% of men). "
                f"Fixes open content to 1B+ people with disabilities worldwide."
            )

        if 'Psychological/UX' in cats:
            insights['All Users'] = (
                f"{len(cats['Psychological/UX'])} UX issues create cognitive friction. "
                f"Poor visual hierarchy increases completion time 20-30%. "
                f"Reducing cognitive load improves conversion 10-15%."
            )

        if 'Performance' in cats:
            insights['Mobile Users'] = (
                "53% of mobile users abandon sites >3s load time. "
                "Performance issues hit slow connections hardest. "
                "Fast sites see 2x higher conversion."
            )

        if 'SEO/Discoverability' in cats:
            insights['Search Visibility'] = (
                "Accessible sites rank higher in search. "
                "Good structure improves SEO 20-40%. "
                "Better metadata reaches millions more users."
            )

        return insights

analyzer = Analyzer()

# ============================================================================
# ENDPOINTS
# ============================================================================
@app.post("/api/audit")
async def audit(
    url: Optional[str] = Form(None),
    html_content: Optional[str] = Form(None),
    screenshots: List[UploadFile] = File(None)
):
    """Main audit: HTML, screenshot(s), or both (at least one required)"""
    try:
        has_html = url and html_content
        has_imgs = screenshots and len(screenshots) > 0

        if not has_html and not has_imgs:
            raise HTTPException(400, "Provide url+html_content OR screenshot(s)")

        # Limit screenshots to 3
        if has_imgs and len(screenshots) > 3:
            raise HTTPException(400, "Maximum 3 screenshots allowed")

        # HTML analysis
        html_res = await analyzer.analyze_html(url, html_content) if has_html else None

        # Vision analysis (single or multi)
        vision_res = None
        if has_imgs:
            images_bytes = [await img.read() for img in screenshots]
            if len(images_bytes) == 1:
                vision_res = await analyzer.analyze_vision(images_bytes[0], url)
            else:
                vision_res = await analyzer.analyze_vision_multi(images_bytes, url)

        # Combine or use single with dynamic scoring
        if html_res and vision_res:
            result = await analyzer.combine(html_res, vision_res)
        elif vision_res:
            # Vision-only: calculate category scores
            category_scores = analyzer._calculate_category_scores(None, vision_res, has_html=False, has_vision=True)
            score = int(
                category_scores['wcag'] * 0.35 +
                category_scores['ux_psychology'] * 0.35 +
                category_scores['visual_design'] * 0.30
            )
            result = {
                'score': score,
                'category_scores': category_scores,
                'summary': vision_res['summary'],
                'issues': vision_res['issues'],
                'metrics': {},
                'analysis_type': vision_res['analysis_type']
            }
        else:  # html_res only
            # HTML-only: calculate category scores
            category_scores = analyzer._calculate_category_scores(html_res, None, has_html=True, has_vision=False)
            score = int(
                category_scores['wcag'] * 0.40 +
                category_scores['ux_psychology'] * 0.25 +
                category_scores['visual_design'] * 0.10 +
                category_scores['seo'] * 0.15 +
                category_scores['performance'] * 0.10
            )
            result = {
                'score': score,
                'category_scores': category_scores,
                'summary': html_res['summary'],
                'issues': html_res['issues'],
                'metrics': html_res.get('metrics', {}),
                'analysis_type': html_res['analysis_type']
            }

        # Generate insights
        who_helps = analyzer.generate_who_helps(result['issues'])

        # Grade
        score = result['score']
        grade = 'A' if score>=90 else 'B' if score>=80 else 'C' if score>=70 else 'D' if score>=60 else 'F'

        # Warnings based on input type
        warnings = []
        if not has_html:
            warnings.append("SEO and Performance scores unavailable without HTML/URL analysis")
            warnings.append("For complete audit, provide both URL and screenshots")
        if not has_imgs:
            warnings.append("Visual Design and UX Psychology scores limited without screenshots")
            warnings.append("For comprehensive visual analysis, upload 1-3 screenshots")

        return {
            "score": score,
            "grade": grade,
            "category_scores": result.get('category_scores', {}),
            "summary": result['summary'],
            "issues": result['issues'],
            "who_this_helps": who_helps,
            "metrics": result.get('metrics', {}),
            "analysis_type": result['analysis_type'],
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/chat")
async def chat(msg: ChatMessage):
    """Follow-up Q&A using Nemotron Nano 9B"""
    try:
        system = "You're an accessibility expert. Answer questions about audits, WCAG, implementation. Be concise."

        context_str = f"\n\nAudit: {json.dumps(msg.context, indent=2)}" if msg.context else ""

        resp = await nim.chat(MODEL_CHAT, [
            {"role": "system", "content": system},
            {"role": "user", "content": msg.message + context_str}
        ], temp=0.7, max_tok=500)

        return {
            "answer": resp['choices'][0]['message']['content'],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(500, str(e))

@app.get("/api/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "models": {"analysis": MODEL_LLM, "vision": MODEL_VISION, "chat": MODEL_CHAT},
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("shutdown")
async def shutdown():
    await nim.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
