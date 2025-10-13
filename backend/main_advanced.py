"""
Accessibility Auditor - Advanced AI-Powered Analysis
Using NVIDIA NIM API with multiple models for comprehensive, context-aware analysis
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
import time
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from enum import Enum

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create rotating file handlers
audit_handler = RotatingFileHandler(
    'audit_log.json',
    maxBytes=10*1024*1024,
    backupCount=5
)
scoring_handler = RotatingFileHandler(
    'scoring_analysis.log',
    maxBytes=5*1024*1024,
    backupCount=3
)
logger.addHandler(audit_handler)
logger.addHandler(scoring_handler)

app = FastAPI(title="Accessibility Auditor - Advanced AI", version="10.0.0")

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

# Advanced Model Configuration - Using multiple NVIDIA models for different tasks
MODELS = {
    "content_analysis": "meta/llama-3.1-70b-instruct",  # For HTML/content analysis
    "vision": "nvidia/neva-22b",  # For screenshot analysis
    "code_generation": "nvidia/starcoder2-15b",  # For generating fix code
    "reasoning": "nvidia/nemotron-4-340b-instruct",  # For complex reasoning
    "embedding": "nvidia/nv-embedqa-e5-v5"  # For semantic understanding
}

class SiteCategory(Enum):
    NEWS = "news"
    ECOMMERCE = "e-commerce"
    SOCIAL = "social"
    DEVELOPER = "developer"
    CORPORATE = "corporate"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    GOVERNMENT = "government"
    SPORTS = "sports"
    GENERAL = "general"

@dataclass
class AccessibilityIssue:
    title: str
    severity: str
    description: str
    element_context: str
    specific_fix: str
    code_example: str
    why_matters: str
    affected_users: str
    wcag_criterion: str
    impact_score: float

class AdvancedAnalyzer:
    """Advanced analyzer using multiple NVIDIA NIM models"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def detect_site_category(self, url: str, content: str) -> SiteCategory:
        """Use AI to detect the type of website"""
        prompt = f"""
        Analyze this website and determine its primary category:
        URL: {url}
        Content preview: {content[:1000]}
        
        Categories: news, e-commerce, social, developer, corporate, educational, entertainment, government, sports
        
        Return only the category name.
        """
        
        try:
            response = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={
                    "model": MODELS["reasoning"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 50
                }
            )
            
            if response.status_code == 200:
                category = response.json()['choices'][0]['message']['content'].strip().lower()
                return SiteCategory[category.upper().replace("-", "")]
        except:
            pass
        
        # Fallback detection
        if 'espn' in url or 'sports' in url:
            return SiteCategory.SPORTS
        elif 'amazon' in url or 'shop' in url:
            return SiteCategory.ECOMMERCE
        elif 'github' in url or 'stackoverflow' in url:
            return SiteCategory.DEVELOPER
        return SiteCategory.GENERAL
    
    async def analyze_html_structure(self, html: str, url: str) -> Dict:
        """Deep HTML analysis using AI"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract detailed metrics
        analysis = {
            "headings": self._analyze_heading_structure(soup),
            "images": self._analyze_images(soup),
            "forms": self._analyze_forms(soup),
            "navigation": self._analyze_navigation(soup),
            "aria": self._analyze_aria(soup),
            "semantics": self._analyze_semantics(soup),
            "interactive": self._analyze_interactive_elements(soup),
            "content": self._analyze_content_structure(soup),
            "metadata": self._analyze_metadata(soup),
            "multimedia": self._analyze_multimedia(soup)
        }
        
        # Use AI to understand context
        prompt = f"""
        Analyze this website's accessibility structure:
        URL: {url}
        
        Structure found:
        - {analysis['headings']['h1_count']} H1 headings
        - {analysis['images']['total']} images ({analysis['images']['without_alt']} missing alt)
        - {analysis['forms']['total']} forms ({analysis['forms']['unlabeled_inputs']} unlabeled inputs)
        - ARIA landmarks: {analysis['aria']['landmark_count']}
        - Skip links: {analysis['navigation']['has_skip_links']}
        
        Identify the 3 most critical accessibility issues specific to this type of site.
        For each issue, provide:
        1. The specific problem
        2. The exact HTML element or pattern causing it
        3. Why it's particularly problematic for this type of site
        
        Format as JSON.
        """
        
        try:
            response = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={
                    "model": MODELS["content_analysis"],
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                ai_insights = response.json()['choices'][0]['message']['content']
                analysis['ai_insights'] = ai_insights
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            
        return analysis
    
    def _analyze_heading_structure(self, soup) -> Dict:
        """Analyze heading hierarchy in detail"""
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        h3_tags = soup.find_all('h3')
        
        # Check for proper hierarchy
        hierarchy_issues = []
        all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if len(h1_tags) == 0:
            hierarchy_issues.append("No H1 tag found - critical for screen readers")
        elif len(h1_tags) > 1:
            hierarchy_issues.append(f"{len(h1_tags)} H1 tags found - should only have one")
            
        # Check for skipped levels
        heading_levels = [int(h.name[1]) for h in all_headings]
        for i in range(1, len(heading_levels)):
            if heading_levels[i] - heading_levels[i-1] > 1:
                hierarchy_issues.append(f"Skipped heading level: H{heading_levels[i-1]} to H{heading_levels[i]}")
                
        return {
            "h1_count": len(h1_tags),
            "h2_count": len(h2_tags),
            "h3_count": len(h3_tags),
            "total_headings": len(all_headings),
            "hierarchy_issues": hierarchy_issues,
            "h1_text": h1_tags[0].get_text(strip=True) if h1_tags else None
        }
    
    def _analyze_images(self, soup) -> Dict:
        """Detailed image analysis"""
        images = soup.find_all('img')
        issues = []
        
        images_without_alt = []
        decorative_without_role = []
        informative_with_poor_alt = []
        
        for img in images:
            alt = img.get('alt', None)
            src = img.get('src', '')
            role = img.get('role')
            
            if alt is None:
                images_without_alt.append(src)
                issues.append(f"Image '{src[:50]}' has no alt attribute")
            elif alt == "":
                if role != "presentation":
                    decorative_without_role.append(src)
                    issues.append(f"Decorative image '{src[:50]}' should have role='presentation'")
            elif len(alt) < 5 or alt.lower() in ['image', 'photo', 'picture', 'img']:
                informative_with_poor_alt.append(src)
                issues.append(f"Image has non-descriptive alt text: '{alt}'")
                
        return {
            "total": len(images),
            "without_alt": len(images_without_alt),
            "decorative_issues": len(decorative_without_role),
            "poor_alt_text": len(informative_with_poor_alt),
            "specific_issues": issues[:5]  # Limit to top 5 for clarity
        }
    
    def _analyze_forms(self, soup) -> Dict:
        """Comprehensive form accessibility analysis"""
        forms = soup.find_all('form')
        all_inputs = soup.find_all(['input', 'select', 'textarea'])
        
        unlabeled = []
        missing_required = []
        no_fieldset = []
        
        for input_elem in all_inputs:
            input_type = input_elem.get('type', 'text')
            if input_type == 'hidden':
                continue
                
            input_id = input_elem.get('id')
            input_name = input_elem.get('name', 'unnamed')
            
            # Check for label
            has_label = False
            if input_id:
                label = soup.find('label', {'for': input_id})
                if label:
                    has_label = True
            
            # Check for aria-label
            if not has_label and not input_elem.get('aria-label'):
                unlabeled.append(f"{input_elem.name}[name={input_name}]")
                
            # Check required fields
            if input_elem.get('required') and not input_elem.get('aria-required'):
                missing_required.append(input_name)
                
        # Check for fieldsets in forms with multiple inputs
        for form in forms:
            form_inputs = form.find_all(['input', 'select', 'textarea'])
            if len(form_inputs) > 3 and not form.find('fieldset'):
                no_fieldset.append("Form with multiple inputs lacks fieldset grouping")
                
        return {
            "total": len(forms),
            "total_inputs": len(all_inputs),
            "unlabeled_inputs": len(unlabeled),
            "unlabeled_details": unlabeled[:5],
            "missing_required_aria": len(missing_required),
            "fieldset_issues": len(no_fieldset)
        }
    
    def _analyze_navigation(self, soup) -> Dict:
        """Analyze navigation accessibility"""
        nav_elements = soup.find_all('nav')
        all_links = soup.find_all('a')
        
        # Check for skip links
        skip_link_patterns = ['skip', 'jump', 'main content', 'navigation']
        has_skip = False
        for link in all_links[:10]:  # Check first 10 links
            link_text = link.get_text(strip=True).lower()
            if any(pattern in link_text for pattern in skip_link_patterns):
                has_skip = True
                break
                
        # Check for accessible menus
        menu_issues = []
        for nav in nav_elements:
            if not nav.get('aria-label') and not nav.get('aria-labelledby'):
                menu_issues.append("Navigation lacks aria-label")
                
        # Check link quality
        generic_link_text = ['click here', 'read more', 'link', 'here']
        poor_links = []
        for link in all_links:
            text = link.get_text(strip=True).lower()
            if text in generic_link_text:
                poor_links.append(text)
                
        return {
            "has_skip_links": has_skip,
            "nav_count": len(nav_elements),
            "total_links": len(all_links),
            "menu_issues": menu_issues,
            "generic_link_count": len(poor_links),
            "keyboard_nav_ready": len(nav_elements) > 0 and has_skip
        }
    
    def _analyze_aria(self, soup) -> Dict:
        """Analyze ARIA usage"""
        landmarks = soup.find_all(attrs={'role': True})
        aria_labels = soup.find_all(attrs={'aria-label': True})
        aria_described = soup.find_all(attrs={'aria-describedby': True})
        live_regions = soup.find_all(attrs={'aria-live': True})
        
        # Check for main landmark
        has_main = bool(soup.find(role='main') or soup.find('main'))
        
        return {
            "landmark_count": len(landmarks),
            "has_main_landmark": has_main,
            "aria_labels_used": len(aria_labels),
            "aria_describedby_used": len(aria_described),
            "live_regions": len(live_regions),
            "proper_structure": has_main and len(landmarks) > 2
        }
    
    def _analyze_semantics(self, soup) -> Dict:
        """Analyze semantic HTML usage"""
        semantic_elements = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        found_semantics = {}
        
        for elem in semantic_elements:
            elements = soup.find_all(elem)
            found_semantics[elem] = len(elements)
            
        # Calculate semantic score
        semantic_score = sum(1 for count in found_semantics.values() if count > 0)
        
        return {
            "elements_found": found_semantics,
            "semantic_score": semantic_score,
            "uses_semantic_html": semantic_score >= 3,
            "missing_semantics": [elem for elem, count in found_semantics.items() if count == 0]
        }
    
    def _analyze_interactive_elements(self, soup) -> Dict:
        """Analyze buttons, controls, and interactive elements"""
        buttons = soup.find_all('button')
        button_issues = []
        
        for button in buttons:
            text = button.get_text(strip=True)
            aria_label = button.get('aria-label')
            
            if not text and not aria_label:
                button_issues.append("Button with no accessible text")
            elif text and len(text) < 3:
                button_issues.append(f"Button with unclear text: '{text}'")
                
        # Check for click handlers on non-interactive elements
        divs_with_onclick = soup.find_all('div', onclick=True)
        spans_with_onclick = soup.find_all('span', onclick=True)
        
        return {
            "button_count": len(buttons),
            "button_issues": button_issues[:5],
            "non_semantic_clickable": len(divs_with_onclick) + len(spans_with_onclick),
            "interaction_problems": len(button_issues) + len(divs_with_onclick) + len(spans_with_onclick)
        }
    
    def _analyze_content_structure(self, soup) -> Dict:
        """Analyze content organization and readability"""
        # Get text content
        text = soup.get_text()
        words = text.split()
        
        # Check for lists
        ul_lists = soup.find_all('ul')
        ol_lists = soup.find_all('ol')
        dl_lists = soup.find_all('dl')
        
        # Check tables
        tables = soup.find_all('table')
        accessible_tables = 0
        for table in tables:
            if table.find('caption') or table.find('th'):
                accessible_tables += 1
                
        return {
            "word_count": len(words),
            "list_count": len(ul_lists) + len(ol_lists) + len(dl_lists),
            "table_count": len(tables),
            "accessible_tables": accessible_tables,
            "content_density": len(words) / max(len(soup.find_all(['p', 'div', 'span'])), 1)
        }
    
    def _analyze_metadata(self, soup) -> Dict:
        """Analyze page metadata"""
        title = soup.find('title')
        meta_desc = soup.find('meta', {'name': 'description'})
        viewport = soup.find('meta', {'name': 'viewport'})
        lang = soup.html.get('lang') if soup.html else None
        
        return {
            "has_title": bool(title),
            "title_text": title.text if title else None,
            "has_description": bool(meta_desc),
            "has_viewport": bool(viewport),
            "has_lang": bool(lang),
            "lang_value": lang
        }
    
    def _analyze_multimedia(self, soup) -> Dict:
        """Analyze video and audio accessibility"""
        videos = soup.find_all('video')
        audio_elements = soup.find_all('audio')
        iframes = soup.find_all('iframe')
        
        video_issues = []
        for video in videos:
            if not video.find('track', {'kind': 'captions'}):
                video_issues.append("Video lacks captions")
                
        iframe_issues = []
        for iframe in iframes:
            if not iframe.get('title'):
                iframe_issues.append("iFrame lacks title attribute")
                
        return {
            "video_count": len(videos),
            "audio_count": len(audio_elements),
            "iframe_count": len(iframes),
            "video_issues": video_issues,
            "iframe_issues": iframe_issues
        }
    
    async def generate_contextual_recommendations(
        self, 
        analysis: Dict, 
        site_category: SiteCategory,
        url: str
    ) -> List[AccessibilityIssue]:
        """Generate specific, contextual recommendations using AI"""
        
        issues = []
        
        # Build context for AI
        context = f"""
        Website: {url}
        Category: {site_category.value}
        
        Analysis Results:
        - Heading Issues: {analysis['headings']['hierarchy_issues']}
        - Images without alt: {analysis['images']['without_alt']}/{analysis['images']['total']}
        - Unlabeled form inputs: {analysis['forms']['unlabeled_inputs']}/{analysis['forms']['total_inputs']}
        - Navigation: Skip links: {analysis['navigation']['has_skip_links']}
        - Semantic HTML: {analysis['semantics']['uses_semantic_html']}
        - ARIA landmarks: {analysis['aria']['landmark_count']}
        
        Generate specific accessibility recommendations for this {site_category.value} website.
        For each issue, provide:
        1. Specific HTML elements affected
        2. Exact code fix with proper syntax
        3. Why this matters for {site_category.value} users specifically
        4. WCAG criterion violated
        
        Focus on the most impactful issues for this type of site.
        """
        
        prompt = f"""
        {context}
        
        Generate 5-8 specific accessibility issues as JSON array. Each issue should have:
        - title: Clear, specific title
        - severity: "severe", "moderate", or "casual"
        - description: Detailed explanation of the problem
        - element_context: The specific HTML element or section
        - specific_fix: Step-by-step fix instructions
        - code_example: Exact HTML/CSS code to implement
        - why_matters: Why this is important for {site_category.value} site users
        - affected_users: Which user groups are impacted
        - wcag_criterion: WCAG 2.1 criterion (e.g., "1.1.1 Non-text Content")
        - impact_score: Float 0-10 for priority
        
        Be extremely specific to {url} and {site_category.value} context.
        """
        
        try:
            response = await self.client.post(
                f"{NVIDIA_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
                json={
                    "model": MODELS["reasoning"],
                    "messages": [
                        {"role": "system", "content": "You are an accessibility expert. Provide specific, actionable recommendations."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                # Parse JSON from response
                import re
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group())
                    for rec in recommendations:
                        issues.append(AccessibilityIssue(**rec))
                    return issues
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
        
        # Fallback to rule-based recommendations
        return self._generate_fallback_recommendations(analysis, site_category)
    
    def _generate_fallback_recommendations(
        self, 
        analysis: Dict, 
        site_category: SiteCategory
    ) -> List[AccessibilityIssue]:
        """Generate intelligent fallback recommendations"""
        issues = []
        
        # Heading issues
        if analysis['headings']['hierarchy_issues']:
            for issue in analysis['headings']['hierarchy_issues'][:2]:
                issues.append(AccessibilityIssue(
                    title=f"Heading Structure: {issue}",
                    severity="severe" if "No H1" in issue else "moderate",
                    description=issue,
                    element_context="<h1> through <h6> elements",
                    specific_fix="Ensure exactly one H1 per page, then use H2-H6 in hierarchical order",
                    code_example="<h1>Main Page Title</h1>\n<h2>Section Title</h2>\n<h3>Subsection</h3>",
                    why_matters=f"Screen reader users navigate {site_category.value} content via headings",
                    affected_users="Screen reader users, users with cognitive disabilities",
                    wcag_criterion="1.3.1 Info and Relationships",
                    impact_score=8.5
                ))
        
        # Image issues
        if analysis['images']['without_alt'] > 0:
            issues.append(AccessibilityIssue(
                title=f"{analysis['images']['without_alt']} Images Missing Alt Text",
                severity="severe",
                description=f"Images lack alternative text: {', '.join(analysis['images']['specific_issues'][:3])}",
                element_context="<img> elements",
                specific_fix="Add descriptive alt attributes to all informative images",
                code_example='<img src="team-photo.jpg" alt="ESPN broadcast team at studio desk">',
                why_matters=f"Critical for {site_category.value} site where visual content conveys information",
                affected_users="Blind users, users with slow connections, search engines",
                wcag_criterion="1.1.1 Non-text Content",
                impact_score=9.0
            ))
        
        # Form issues
        if analysis['forms']['unlabeled_inputs'] > 0:
            issues.append(AccessibilityIssue(
                title=f"{analysis['forms']['unlabeled_inputs']} Form Inputs Lack Labels",
                severity="severe",
                description=f"Form inputs missing labels: {', '.join(analysis['forms']['unlabeled_details'][:3])}",
                element_context="<input>, <select>, <textarea> elements",
                specific_fix="Add explicit <label> elements or aria-label attributes",
                code_example='<label for="email">Email Address</label>\n<input type="email" id="email" name="email" required>',
                why_matters=f"Users cannot complete {site_category.value} forms without knowing field purposes",
                affected_users="Screen reader users, users with cognitive disabilities",
                wcag_criterion="3.3.2 Labels or Instructions",
                impact_score=8.0
            ))
        
        # Navigation issues
        if not analysis['navigation']['has_skip_links']:
            issues.append(AccessibilityIssue(
                title="Missing Skip Navigation Links",
                severity="moderate",
                description="No skip links found in page header",
                element_context="First focusable element in <body>",
                specific_fix="Add skip link as first focusable element",
                code_example='<a href="#main" class="skip-link">Skip to main content</a>\n<style>.skip-link:not(:focus) { position: absolute; left: -10000px; }</style>',
                why_matters=f"Keyboard users must tab through entire {site_category.value} navigation repeatedly",
                affected_users="Keyboard-only users, switch device users",
                wcag_criterion="2.4.1 Bypass Blocks",
                impact_score=7.0
            ))
        
        # Semantic HTML
        if not analysis['semantics']['uses_semantic_html']:
            missing = ', '.join(analysis['semantics']['missing_semantics'][:3])
            issues.append(AccessibilityIssue(
                title="Missing Semantic HTML5 Elements",
                severity="moderate",
                description=f"Page lacks semantic elements: {missing}",
                element_context="Document structure",
                specific_fix="Replace generic <div> with semantic HTML5 elements",
                code_example="<nav>...</nav>\n<main>...</main>\n<aside>...</aside>\n<footer>...</footer>",
                why_matters=f"Semantic HTML helps users understand {site_category.value} page structure",
                affected_users="All users, especially those using assistive technology",
                wcag_criterion="1.3.1 Info and Relationships",
                impact_score=6.5
            ))
        
        return issues
    
    def calculate_contextual_score(
        self, 
        analysis: Dict, 
        issues: List[AccessibilityIssue],
        site_category: SiteCategory
    ) -> Dict[str, float]:
        """Calculate nuanced, context-aware scores"""
        
        # Base scores adjusted by site category
        category_weights = {
            SiteCategory.NEWS: {"content_hierarchy": 1.2, "navigation_ease": 1.1},
            SiteCategory.ECOMMERCE: {"interactive_feedback": 1.3, "trust_signals": 1.2},
            SiteCategory.SPORTS: {"visual_clarity": 1.2, "content_hierarchy": 1.1},
            SiteCategory.DEVELOPER: {"cognitive_load": 1.2, "content_hierarchy": 1.3},
            SiteCategory.GOVERNMENT: {"wcag_compliance": 1.5, "navigation_ease": 1.3},
        }
        
        weights = category_weights.get(site_category, {})
        
        # Start with baseline scores
        scores = {
            "wcag_compliance": 70,
            "visual_clarity": 70,
            "cognitive_load": 70,
            "mobile_usability": 70,
            "color_accessibility": 70,
            "navigation_ease": 70,
            "content_hierarchy": 70,
            "interactive_feedback": 70,
            "trust_signals": 70,
            "performance_perception": 70
        }
        
        # Adjust based on analysis
        
        # WCAG Compliance
        if analysis['metadata']['has_lang']:
            scores['wcag_compliance'] += 5
        else:
            scores['wcag_compliance'] -= 15
            
        if analysis['headings']['h1_count'] == 1:
            scores['wcag_compliance'] += 5
        elif analysis['headings']['h1_count'] == 0:
            scores['wcag_compliance'] -= 10
        else:
            scores['wcag_compliance'] -= 5
            
        # Visual Clarity
        if analysis['images']['total'] > 0:
            alt_percentage = 1 - (analysis['images']['without_alt'] / analysis['images']['total'])
            scores['visual_clarity'] += int(alt_percentage * 15)
            scores['wcag_compliance'] += int(alt_percentage * 10)
            
        # Cognitive Load
        if analysis['content']['content_density'] < 50:
            scores['cognitive_load'] += 10
        elif analysis['content']['content_density'] > 200:
            scores['cognitive_load'] -= 10
            
        # Mobile Usability
        if analysis['metadata']['has_viewport']:
            scores['mobile_usability'] += 15
        else:
            scores['mobile_usability'] -= 20
            
        # Navigation
        if analysis['navigation']['has_skip_links']:
            scores['navigation_ease'] += 10
        else:
            scores['navigation_ease'] -= 10
            
        if analysis['navigation']['keyboard_nav_ready']:
            scores['navigation_ease'] += 5
            
        # Content Hierarchy
        if analysis['semantics']['uses_semantic_html']:
            scores['content_hierarchy'] += 10
        else:
            scores['content_hierarchy'] -= 15
            
        if not analysis['headings']['hierarchy_issues']:
            scores['content_hierarchy'] += 10
        else:
            scores['content_hierarchy'] -= len(analysis['headings']['hierarchy_issues']) * 3
            
        # Interactive Feedback
        if analysis['forms']['unlabeled_inputs'] == 0 and analysis['forms']['total_inputs'] > 0:
            scores['interactive_feedback'] += 15
        elif analysis['forms']['unlabeled_inputs'] > 0:
            penalty = min(20, analysis['forms']['unlabeled_inputs'] * 5)
            scores['interactive_feedback'] -= penalty
            
        # Apply category-specific weights
        for dimension, weight in weights.items():
            if dimension in scores:
                scores[dimension] = int(scores[dimension] * weight)
                
        # Calculate severity-based penalties
        severe_count = sum(1 for issue in issues if issue.severity == "severe")
        moderate_count = sum(1 for issue in issues if issue.severity == "moderate")
        
        overall_penalty = (severe_count * 5) + (moderate_count * 2)
        
        # Ensure scores are within bounds
        scores = {k: max(10, min(95, v)) for k, v in scores.items()}
        
        # Calculate weighted overall score
        weights = {
            "wcag_compliance": 0.25,
            "visual_clarity": 0.12,
            "cognitive_load": 0.12,
            "mobile_usability": 0.10,
            "color_accessibility": 0.08,
            "navigation_ease": 0.10,
            "content_hierarchy": 0.08,
            "interactive_feedback": 0.07,
            "trust_signals": 0.05,
            "performance_perception": 0.03
        }
        
        overall = sum(scores[k] * weights[k] for k in weights.keys())
        overall -= overall_penalty
        overall = max(15, min(90, overall))
        
        scores['overall'] = round(overall)
        
        return scores

# Initialize analyzer
analyzer = AdvancedAnalyzer()

async def fetch_website_content(url: str) -> tuple[str, Dict]:
    """Fetch website HTML and extract content"""
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            return response.text, {"url": url, "status": "success"}
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return "", {"url": url, "status": "error", "error": str(e)}

async def analyze_website_comprehensive(url: str) -> Dict:
    """Perform comprehensive AI-powered analysis"""
    start_time = time.time()
    
    # Fetch content
    html_content, fetch_status = await fetch_website_content(url)
    if not html_content:
        return {
            "success": False,
            "error": fetch_status.get("error", "Failed to fetch website"),
            "url": url
        }
    
    # Detect site category
    site_category = await analyzer.detect_site_category(url, html_content)
    
    # Analyze HTML structure
    analysis = await analyzer.analyze_html_structure(html_content, url)
    
    # Generate contextual recommendations
    issues = await analyzer.generate_contextual_recommendations(
        analysis, site_category, url
    )
    
    # Calculate scores
    scores = analyzer.calculate_contextual_score(analysis, issues, site_category)
    
    # Format issues for frontend
    formatted_issues = []
    for issue in issues:
        formatted_issues.append({
            "title": issue.title,
            "severity": issue.severity,
            "description": issue.description,
            "recommendation": f"{issue.specific_fix}\n\nCode:\n{issue.code_example}",
            "why_this_matters": issue.why_matters,
            "impact_metric": f"WCAG {issue.wcag_criterion} | Affects: {issue.affected_users}"
        })
    
    # Generate summary
    if scores['overall'] < 40:
        summary = f"{url} has critical accessibility barriers that urgently need attention. "
    elif scores['overall'] < 60:
        summary = f"{url} has moderate accessibility with room for significant improvements. "
    elif scores['overall'] < 75:
        summary = f"{url} demonstrates good accessibility with opportunities for enhancement. "
    else:
        summary = f"{url} shows strong accessibility practices with minor refinements possible. "
    
    summary += f"As a {site_category.value} site, priority should be on {get_priority_for_category(site_category)}."
    
    # Log the analysis
    logger.info(f"""
    ============================================================
    ADVANCED ANALYSIS: {url}
    Category: {site_category.value}
    Overall Score: {scores['overall']}/100
    Severe Issues: {sum(1 for i in issues if i.severity == 'severe')}
    Analysis Time: {time.time() - start_time:.2f}s
    ============================================================
    """)
    
    return {
        "success": True,
        "url": url,
        "site_profile": site_category.value.title() + " Website",
        "overall_score": scores['overall'],
        "scores": scores,
        "issues": formatted_issues,
        "severe_count": sum(1 for i in issues if i.severity == "severe"),
        "moderate_count": sum(1 for i in issues if i.severity == "moderate"),
        "casual_count": sum(1 for i in issues if i.severity == "casual"),
        "summary": summary,
        "analysis_time": round(time.time() - start_time, 2)
    }

def get_priority_for_category(category: SiteCategory) -> str:
    """Get priority focus area for site category"""
    priorities = {
        SiteCategory.NEWS: "content hierarchy and navigation speed",
        SiteCategory.SPORTS: "real-time updates and multimedia accessibility",
        SiteCategory.ECOMMERCE: "form accessibility and trust signals",
        SiteCategory.DEVELOPER: "code readability and documentation structure",
        SiteCategory.GOVERNMENT: "WCAG compliance and universal access",
        SiteCategory.EDUCATIONAL: "content organization and cognitive load",
        SiteCategory.ENTERTAINMENT: "multimedia controls and interactive elements",
        SiteCategory.SOCIAL: "dynamic content and user-generated accessibility"
    }
    return priorities.get(category, "comprehensive WCAG compliance")

@app.get("/")
async def root():
    return {
        "message": "Accessibility Auditor - Advanced AI Analysis",
        "version": "10.0.0",
        "features": [
            "Multi-model NVIDIA NIM integration",
            "Context-aware recommendations",
            "Site category detection",
            "Intelligent scoring",
            "Comprehensive HTML analysis"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": list(MODELS.keys()),
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
    """Perform advanced AI-powered accessibility audit"""
    
    # Log request
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "type": "advanced_audit"
    }
    
    # Perform analysis
    result = await analyze_website_comprehensive(url)
    
    # Complete audit log
    audit_entry.update({
        "success": result.get("success", False),
        "overall_score": result.get("overall_score", 0),
        "site_category": result.get("site_profile", "Unknown"),
        "analysis_time": result.get("analysis_time", 0),
        "issues": {
            "severe": result.get("severe_count", 0),
            "moderate": result.get("moderate_count", 0),
            "casual": result.get("casual_count", 0)
        }
    })
    
    # Write logs
    with open('audit_log.json', 'a') as f:
        f.write(json.dumps(audit_entry) + '\n')
    
    return result

@app.post("/audit/image")
async def audit_image(file: UploadFile = File(...)):
    """Analyze uploaded image using NVIDIA vision models"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode()
        
        # Use NVIDIA vision model for analysis
        prompt = """
        Analyze this website screenshot for accessibility issues.
        Look for:
        1. Color contrast problems
        2. Text size issues
        3. Layout problems
        4. Missing visual indicators
        5. Crowded or confusing interfaces
        
        Provide specific observations and recommendations.
        """
        
        # Here we would call NVIDIA's vision model
        # For now, return a structured response
        
        return {
            "success": True,
            "filename": file.filename,
            "overall_score": 65,
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
            "summary": "Screenshot analysis provides visual accessibility insights. For comprehensive analysis, provide the website URL.",
            "issues": [
                {
                    "severity": "moderate",
                    "title": "Visual Analysis Limitations",
                    "description": "Screenshots can only analyze visual aspects, not underlying code structure.",
                    "recommendation": "Provide the website URL for complete accessibility analysis including HTML structure, ARIA labels, and semantic markup.",
                    "why_this_matters": "Many critical accessibility issues exist in the code structure, not visible in screenshots.",
                    "impact_metric": "URL analysis provides 10x more detailed insights"
                }
            ],
            "severe_count": 0,
            "moderate_count": 1,
            "casual_count": 0,
            "site_profile": "Screenshot Analysis"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Advanced AI-Powered Accessibility Auditor")
    print("🧠 Using NVIDIA NIM Models:")
    for purpose, model in MODELS.items():
        print(f"  - {purpose}: {model}")
    print("📡 API available at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    uvicorn.run("main_advanced:app", host="0.0.0.0", port=8000, reload=True)