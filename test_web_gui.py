#!/usr/bin/env python3
"""Test web GUI functionality"""
import sys
import time
import requests
from pathlib import Path
import subprocess
import signal

def test_web_gui():
    """Test web GUI startup and basic endpoints"""
    print("=" * 60)
    print("TEST: Web GUI Functionality")
    print("=" * 60)

    # Start web GUI server in background
    print("\n1. Starting web GUI server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "gui.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for server to start
    print("   Waiting for server to start...")
    time.sleep(5)

    try:
        # Test health endpoint
        print("\n2. Testing health endpoint...")
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")

        if response.status_code == 200:
            print("   [PASS] Health endpoint working")
        else:
            print("   [FAIL] Health endpoint failed")
            return False

        # Test main page
        print("\n3. Testing main page...")
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200 and "Website Status Checker" in response.text:
            print("   [PASS] Main page loads correctly")
        else:
            print("   [FAIL] Main page failed")
            return False

        # Test API docs
        print("\n4. Testing API documentation...")
        response = requests.get("http://localhost:8000/api/docs", timeout=5)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   [PASS] API docs accessible")
        else:
            print("   [FAIL] API docs failed")
            return False

        # Test metrics endpoint
        print("\n5. Testing metrics endpoint...")
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   [PASS] Metrics endpoint working")
        else:
            print("   [FAIL] Metrics endpoint failed")
            return False

        print("\n" + "=" * 60)
        print("[SUCCESS] Web GUI tests passed!")
        print("=" * 60)
        return True

    except requests.exceptions.ConnectionError as e:
        print(f"   [FAIL] Connection error: {e}")
        return False

    except Exception as e:
        print(f"   [FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean shutdown
        print("\n6. Shutting down server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("   Server stopped gracefully")
        except subprocess.TimeoutExpired:
            process.kill()
            print("   Server killed")

if __name__ == "__main__":
    success = test_web_gui()
    sys.exit(0 if success else 1)
