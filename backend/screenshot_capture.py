"""
Screenshot capture module using Pyppeteer for URL analysis
"""

import asyncio
import base64
from io import BytesIO
from typing import Optional

try:
    from pyppeteer import launch
    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False
    print("Pyppeteer not installed. URL screenshot capture will be limited.")

async def capture_screenshot_from_url(url: str, width: int = 1920, height: int = 1080) -> Optional[str]:
    """
    Capture a screenshot of a URL and return as base64 string
    
    Args:
        url: The URL to capture
        width: Viewport width
        height: Viewport height
    
    Returns:
        Base64 encoded screenshot or None if capture fails
    """
    if not PYPPETEER_AVAILABLE:
        return None
    
    browser = None
    try:
        # Launch headless browser
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-gpu'
            ]
        })
        
        # Create new page
        page = await browser.newPage()
        
        # Set viewport size
        await page.setViewport({'width': width, 'height': height})
        
        # Navigate to URL with timeout
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
        
        # Wait a bit for dynamic content
        await asyncio.sleep(2)
        
        # Take screenshot
        screenshot_bytes = await page.screenshot({
            'type': 'jpeg',
            'quality': 90,
            'fullPage': False  # Just capture viewport
        })
        
        # Convert to base64
        screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        return screenshot_base64
        
    except Exception as e:
        print(f"Error capturing screenshot: {str(e)}")
        return None
    
    finally:
        if browser:
            await browser.close()

async def extract_html_from_url(url: str) -> Optional[str]:
    """
    Extract HTML content from a URL
    
    Args:
        url: The URL to extract HTML from
    
    Returns:
        HTML content or None if extraction fails
    """
    if not PYPPETEER_AVAILABLE:
        return None
    
    browser = None
    try:
        browser = await launch({
            'headless': True,
            'args': ['--no-sandbox', '--disable-setuid-sandbox']
        })
        
        page = await browser.newPage()
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
        
        # Get the HTML content
        html_content = await page.content()
        
        return html_content[:10000]  # Limit HTML size for processing
        
    except Exception as e:
        print(f"Error extracting HTML: {str(e)}")
        return None
    
    finally:
        if browser:
            await browser.close()

# Alternative using httpx for simple cases
async def capture_screenshot_fallback(url: str) -> str:
    """
    Fallback method when Pyppeteer is not available
    Returns a placeholder message
    """
    return None