#!/usr/bin/env python3
"""
Test script to verify NVIDIA vision API is working with real analysis
"""

import requests
import json
import sys
from pathlib import Path

def test_health():
    """Test API health endpoint"""
    response = requests.get("http://localhost:8000/health")
    print("Health Check:", response.json())
    return response.json().get("vision_model_configured", False)

def test_url_analysis():
    """Test URL analysis with screenshot"""
    print("\n📸 Testing URL Analysis...")
    
    # Test with a real website
    test_urls = [
        "https://example.com",
        "https://google.com"
    ]
    
    for url in test_urls:
        print(f"\nAnalyzing: {url}")
        
        response = requests.post(
            "http://localhost:8000/audit/url",
            data={"url": url}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['total_issues']} issues")
            print(f"   Critical: {data['critical_count']}")
            print(f"   Major: {data['major_count']}")
            print(f"   Minor: {data['minor_count']}")
            
            if data.get('scores'):
                print("\n   Scores:")
                for key, value in data['scores'].items():
                    print(f"   - {key}: {value}/100")
            
            # Check if we're getting real or sample data
            if "sample" in data.get('summary', '').lower() or data.get('screenshot_captured') == False:
                print("   ⚠️  Note: Using fallback sample data")
            else:
                print("   ✨ Using real vision analysis!")
                
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
    
    return None

def test_image_upload():
    """Test direct image upload"""
    print("\n🖼️  Testing Image Upload...")
    
    # Create a test image
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Create test image with accessibility issues
        img = Image.new('RGB', (1200, 800), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add low contrast text (accessibility issue)
        draw.text((50, 50), "Low Contrast Text", fill='#f0f0f0')
        
        # Add normal text
        draw.text((50, 100), "Normal Text", fill='black')
        
        # Small clickable area (accessibility issue)
        draw.rectangle([50, 200, 70, 220], fill='blue')
        draw.text((80, 200), "Tiny Button", fill='black')
        
        # Save to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Upload
        files = {'file': ('test.png', img_bytes, 'image/png')}
        response = requests.post("http://localhost:8000/audit/image", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Analysis complete")
            print(f"   Issues found: {data['total_issues']}")
            print(f"   Summary: {data['summary'][:100]}...")
            return data
        else:
            print(f"❌ Error: {response.status_code}")
            
    except ImportError:
        print("   ⚠️  Pillow not installed for image testing")
    
    return None

def main():
    print("🔍 Testing NVIDIA Vision API Integration\n")
    print("=" * 50)
    
    # Check health
    if not test_health():
        print("\n⚠️  Warning: NVIDIA API key might not be configured")
    
    # Test URL analysis
    url_result = test_url_analysis()
    
    # Test image upload
    img_result = test_image_upload()
    
    print("\n" + "=" * 50)
    print("\n📊 Test Summary:")
    
    if url_result and img_result:
        # Check if we're getting different results for different inputs
        if url_result.get('summary') != img_result.get('summary'):
            print("✅ Different analyses for different inputs - Real vision API working!")
        else:
            print("⚠️  Same results for different inputs - Likely using fallback data")
    
    print("\n💡 To get real vision analysis:")
    print("   1. Ensure NVIDIA_API_KEY is set in .env")
    print("   2. Check server logs: tail -f server.log")
    print("   3. Look for 'Successfully got vision analysis response' in logs")

if __name__ == "__main__":
    main()