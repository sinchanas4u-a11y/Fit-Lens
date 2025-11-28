"""
Test backend API endpoints
"""
import requests
import time

BASE_URL = "http://localhost:5000"

print("Testing Backend API...")
print("=" * 50)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ERROR: {e}")
    print("   Make sure backend is running: python app.py")
    exit(1)

# Test 2: Start camera
print("\n2. Testing camera start...")
try:
    response = requests.post(f"{BASE_URL}/api/camera/start")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✓ Camera started successfully!")
        print("   Check backend terminal for 'Starting camera...' message")
    else:
        print("   ✗ Failed to start camera")
except Exception as e:
    print(f"   ERROR: {e}")

# Wait a bit
print("\n3. Waiting 2 seconds for camera to initialize...")
time.sleep(2)

# Test 3: Stop camera
print("\n4. Testing camera stop...")
try:
    response = requests.post(f"{BASE_URL}/api/camera/stop")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 50)
print("API Test Complete!")
print("\nIf all tests passed, the backend is working correctly.")
print("Now start the frontend with: cd frontend && npm start")
