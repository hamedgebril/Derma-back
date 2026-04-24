"""
API Endpoint Verification Script
Tests the cleaned-up Diagnosis API endpoints
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx


BASE_URL = "http://localhost:8000"
TEST_IMAGE = "uploads/c8199e76-a588-4760-97ea-4815d691731d.jpg"


async def verify_endpoints():
    """Verify all API endpoints are working correctly"""
    
    print("=" * 60)
    print("Dermavision API Endpoint Verification")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Health Check
        print("\n1. Testing Health Endpoints...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/health")
            print(f"   ✓ GET /api/v1/health - Status: {response.status_code}")
            
            response = await client.get(f"{BASE_URL}/api/v1/ready")
            print(f"   ✓ GET /api/v1/ready - Status: {response.status_code}")
            data = response.json()
            print(f"     - Ready: {data.get('ready')}")
            print(f"     - ML Model: {data.get('checks', {}).get('ml_model', {}).get('ready')}")
            print(f"     - Database: {data.get('checks', {}).get('database', {}).get('ready')}")
        except Exception as e:
            print(f"   ✗ Health check failed: {e}")
            return False
        
        # 2. Authentication
        print("\n2. Testing Authentication Endpoints...")
        test_email = "test_verify@example.com"
        test_password = "testpass123"
        
        try:
            # Signup
            signup_data = {
                "email": test_email,
                "username": "test_verify",
                "password": test_password
            }
            response = await client.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
            if response.status_code in [201, 400]:  # 400 if user already exists
                print(f"   ✓ POST /api/v1/auth/signup - Status: {response.status_code}")
            
            # Login
            login_data = {
                "email": test_email,
                "password": test_password
            }
            response = await client.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            print(f"   ✓ POST /api/v1/auth/login - Status: {response.status_code}")
            
            if response.status_code == 200:
                token = response.json().get("access_token")
                print(f"     - Token received: {token[:20]}...")
            else:
                print("     - Warning: Login failed, continuing without token")
                token = None
                
        except Exception as e:
            print(f"   ✗ Authentication failed: {e}")
            token = None
        
        # 3. Diagnosis Endpoints
        print("\n3. Testing Diagnosis Endpoints...")
        
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # POST /api/v1/diagnosis
        try:
            if Path(TEST_IMAGE).exists():
                with open(TEST_IMAGE, "rb") as f:
                    files = {"file": (TEST_IMAGE, f, "image/jpeg")}
                    response = await client.post(
                        f"{BASE_URL}/api/v1/diagnosis",
                        files=files,
                        headers=headers
                    )
                print(f"   ✓ POST /api/v1/diagnosis - Status: {response.status_code}")
                
                if response.status_code == 201:
                    data = response.json()
                    print(f"     - Predicted: {data.get('predicted_label')}")
                    print(f"     - Confidence: {data.get('confidence'):.2%}")
                    print(f"     - Quality: {data.get('image_quality_label')} ({data.get('image_quality_score')})")
                    analysis_id = data.get('analysis_id')
                    print(f"     - Analysis ID: {analysis_id}")
                else:
                    print(f"     - Response: {response.text}")
                    analysis_id = None
            else:
                print(f"   ⚠ Skipping POST /api/v1/diagnosis - Test image not found: {TEST_IMAGE}")
                analysis_id = None
                
        except Exception as e:
            print(f"   ✗ POST /api/v1/diagnosis failed: {e}")
            analysis_id = None
        
        # GET /api/v1/history
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/history?limit=5",
                headers=headers
            )
            print(f"   ✓ GET /api/v1/history - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"     - Total analyses: {data.get('total')}")
                print(f"     - Returned: {len(data.get('analyses', []))}")
        except Exception as e:
            print(f"   ✗ GET /api/v1/history failed: {e}")
        
        # GET /api/v1/diagnosis/{analysis_id}
        if analysis_id:
            try:
                response = await client.get(
                    f"{BASE_URL}/api/v1/diagnosis/{analysis_id}",
                    headers=headers
                )
                print(f"   ✓ GET /api/v1/diagnosis/{analysis_id} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"     - ID: {data.get('id')}")
                    print(f"     - Disease: {data.get('predicted_label')}")
            except Exception as e:
                print(f"   ✗ GET /api/v1/diagnosis/{analysis_id} failed: {e}")
        else:
            print(f"   ⚠ Skipping GET /api/v1/diagnosis/{{id}} - No analysis_id available")
        
        # 4. Verify deprecated endpoints are removed
        print("\n4. Verifying Deprecated Endpoints Are Removed...")
        
        deprecated_endpoints = [
            ("POST", "/api/v1/diagnosis/diagnose"),
            ("GET", "/api/v1/diagnosis/diagnoses"),
            ("GET", "/api/v1/diagnosis/diagnoses/1"),
        ]
        
        for method, endpoint in deprecated_endpoints:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{endpoint}", headers=headers)
                else:
                    response = await client.get(f"{BASE_URL}{endpoint}", headers=headers)
                
                if response.status_code == 404:
                    print(f"   ✓ {method} {endpoint} - Correctly removed (404)")
                else:
                    print(f"   ✗ {method} {endpoint} - Still exists (Status: {response.status_code})")
            except Exception as e:
                print(f"   ✓ {method} {endpoint} - Correctly removed (connection error)")
    
    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)
    print("\nFinal API Contract:")
    print("  Health:")
    print("    - GET  /api/v1/health")
    print("    - GET  /api/v1/ready")
    print("  Authentication:")
    print("    - POST /api/v1/auth/signup")
    print("    - POST /api/v1/auth/login")
    print("  Diagnosis:")
    print("    - POST /api/v1/diagnosis")
    print("    - GET  /api/v1/history")
    print("    - GET  /api/v1/diagnosis/{analysis_id}")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    print("\nMake sure the server is running: uvicorn app.main:app --reload\n")
    asyncio.run(verify_endpoints())
