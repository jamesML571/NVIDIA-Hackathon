#!/usr/bin/env python3
"""
Test script to verify the deployment is working correctly
Tests both backend API and basic functionality
"""
import sys
import requests
import time

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_health_check():
    """Test if backend is running and responding"""
    print("Testing backend health check...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   Version: {data.get('version')}")
            print(f"   Model: {data.get('model')}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure the backend is running on port 8000")
        return False

def test_api_structure():
    """Test if API endpoints are accessible"""
    print("\nTesting API documentation...")
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API documentation accessible at http://localhost:8000/docs")
            return True
        else:
            print(f"❌ API docs returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot access API docs: {e}")
        return False

def test_audit_endpoint():
    """Test the audit endpoint with sample data"""
    print("\nTesting audit endpoint...")
    try:
        test_data = {
            "url": "https://example.com",
            "html_content": """
            <!DOCTYPE html>
            <html lang="en">
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Page</h1>
                <img src="test.jpg">
                <p>Some content</p>
            </body>
            </html>
            """
        }

        response = requests.post(
            "http://localhost:8000/api/audit",
            data=test_data,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ Audit endpoint working")
            print(f"   Score: {data.get('score', 'N/A')}")
            print(f"   Grade: {data.get('grade', 'N/A')}")
            print(f"   Issues found: {len(data.get('issues', []))}")
            return True
        else:
            print(f"❌ Audit endpoint returned status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Audit endpoint error: {e}")
        return False

def main():
    print("=" * 60)
    print("NVIDIA Accessibility Auditor - Deployment Test")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Health Check", test_health_check()))
    time.sleep(1)
    results.append(("API Documentation", test_api_structure()))
    time.sleep(1)
    results.append(("Audit Endpoint", test_audit_endpoint()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Deployment is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
