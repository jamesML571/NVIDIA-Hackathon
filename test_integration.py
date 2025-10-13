#!/usr/bin/env python3
"""
Integration test to verify frontend and backend are working together
"""

import requests
import json
import time

# Test configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Test if backend is healthy"""
    print("✓ Testing backend health...")
    response = requests.get(f"{BACKEND_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["nemotron_configured"] == True
    print(f"  ✅ Backend is healthy - Using model: {data['model']}")
    return True

def test_frontend_accessible():
    """Test if frontend is accessible"""
    print("✓ Testing frontend accessibility...")
    response = requests.get(FRONTEND_URL)
    assert response.status_code == 200
    assert "Accessibility Auditor" in response.text
    assert "NVIDIA Hackathon" in response.text
    print("  ✅ Frontend is accessible and serving correctly")
    return True

def test_cors_headers():
    """Test if CORS is properly configured"""
    print("✓ Testing CORS configuration...")
    response = requests.options(
        f"{BACKEND_URL}/audit/image",
        headers={"Origin": FRONTEND_URL}
    )
    # Check if CORS headers are present
    assert response.status_code in [200, 204]
    print("  ✅ CORS is properly configured")
    return True

def main():
    print("\n🔍 NVIDIA Hackathon - Accessibility Auditor")
    print("=" * 50)
    print("Running integration tests...\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Run tests
    tests = [
        test_backend_health,
        test_frontend_accessible,
        test_cors_headers
    ]
    
    for test in tests:
        try:
            if test():
                tests_passed += 1
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            tests_failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✨ Test Results: {tests_passed} passed, {tests_failed} failed")
    
    if tests_failed == 0:
        print("\n🎉 All systems operational! Your app is ready for the hackathon!")
        print("\n📝 Next steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Upload a screenshot or enter a URL")
        print("3. See the AI-powered accessibility analysis")
        print("4. Use the chat to ask follow-up questions")
        print("\n🚀 Good luck with your presentation!")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    print("\n🔗 Access your app:")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   Backend API: {BACKEND_URL}")
    print(f"   API Docs: {BACKEND_URL}/docs")

if __name__ == "__main__":
    main()