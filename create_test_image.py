#!/usr/bin/env python3
"""
Create a test image with accessibility issues for demo
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create a test image with accessibility issues
width, height = 800, 600
image = Image.new('RGB', (width, height), color='white')
draw = ImageDraw.Draw(image)

# Draw low contrast text (accessibility issue)
draw.text((50, 50), "Low Contrast Text", fill='#cccccc')

# Draw normal text
draw.text((50, 100), "Normal Text", fill='black')

# Draw a rectangle without proper labeling
draw.rectangle([50, 150, 200, 250], fill='blue')

# Draw very small text (accessibility issue)
try:
    # Try to use a specific font, fallback to default if not available
    font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 8)
    font_normal = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
except:
    font_small = ImageFont.load_default()
    font_normal = ImageFont.load_default()

draw.text((50, 300), "This text is too small to read easily", fill='black', font=font_small)
draw.text((50, 350), "This text is properly sized", fill='black', font=font_normal)

# Add a button-like element with poor contrast
draw.rectangle([50, 400, 200, 450], fill='#f0f0f0', outline='#e0e0e0')
draw.text((100, 415), "Click Me", fill='#aaaaaa')

# Save the test image
output_path = 'test_website_screenshot.jpg'
image.save(output_path, 'JPEG')
print(f"✅ Test image created: {output_path}")
print("\n🎯 This image contains several accessibility issues:")
print("  • Low contrast text")
print("  • Very small font size")
print("  • Poor button contrast")
print("  • Unlabeled UI elements")
print("\nUpload this image to test your accessibility auditor!")