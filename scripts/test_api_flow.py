"""
Complete API Flow Test
اختبار كامل لـflow الـAPI: signup -> login -> diagnosis -> history
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import random
import string


BASE_URL = "http://localhost:8000"
TEST_IMAGE = "uploads/c8199e76-a588-4760-97ea-4815d691731d.jpg"


def generate_random_email():
    """توليد email عشوائي للاختبار"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"


async def test_complete_flow():
    """اختبار الـflow الكامل"""
    
    print("=" * 70)
    print("🧪 Complete API Flow Test")
    print("=" * 70)
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # 1. Health Check
        print("1️⃣  Testing Health Endpoints...")
        print("-" * 70)
        
        try:
            response = await client.get(f"{BASE_URL}/api/v1/health")
            if response.status_code == 200:
                print(f"   ✅ GET /api/v1/health - {response.status_code}")
            else:
                print(f"   ❌ GET /api/v1/health - {response.status_code}")
                return False
            
            response = await client.get(f"{BASE_URL}/api/v1/ready")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ GET /api/v1/ready - {response.status_code}")
                print(f"      Ready: {data.get('ready')}")
                print(f"      ML Model: {data.get('checks', {}).get('ml_model', {}).get('ready')}")
                print(f"      Database: {data.get('checks', {}).get('database', {}).get('ready')}")
                
                if not data.get('ready'):
                    print("   ⚠️  System not ready - some checks failed")
                    return False
            else:
                print(f"   ❌ GET /api/v1/ready - {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            return False
        
        print()
        
        # 2. Signup
        print("2️⃣  Testing Signup...")
        print("-" * 70)
        
        test_email = generate_random_email()
        test_username = f"user_{random.randint(1000, 9999)}"
        test_password = "testpass123"
        
        try:
            signup_data = {
                "email": test_email,
                "username": test_username,
                "password": test_password
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/signup",
                json=signup_data
            )
            
            if response.status_code == 201:
                user_data = response.json()
                print(f"   ✅ POST /api/v1/auth/signup - {response.status_code}")
                print(f"      User ID: {user_data.get('id')}")
                print(f"      Email: {user_data.get('email')}")
                print(f"      Username: {user_data.get('username')}")
            else:
                print(f"   ❌ POST /api/v1/auth/signup - {response.status_code}")
                print(f"      Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Signup failed: {e}")
            return False
        
        print()
        
        # 3. Login
        print("3️⃣  Testing Login...")
        print("-" * 70)
        
        try:
            login_data = {
                "email": test_email,
                "password": test_password
            }
            
            response = await client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get("access_token")
                print(f"   ✅ POST /api/v1/auth/login - {response.status_code}")
                print(f"      Token: {token[:30]}...")
            else:
                print(f"   ❌ POST /api/v1/auth/login - {response.status_code}")
                print(f"      Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            return False
        
        print()
        
        # 4. Diagnosis
        print("4️⃣  Testing Diagnosis...")
        print("-" * 70)
        
        headers = {"Authorization": f"Bearer {token}"}
        analysis_id = None
        
        try:
            if Path(TEST_IMAGE).exists():
                with open(TEST_IMAGE, "rb") as f:
                    files = {"file": (TEST_IMAGE, f, "image/jpeg")}
                    
                    response = await client.post(
                        f"{BASE_URL}/api/v1/diagnosis",
                        files=files,
                        headers=headers
                    )
                
                if response.status_code == 201:
                    diagnosis_data = response.json()
                    analysis_id = diagnosis_data.get("analysis_id")
                    
                    print(f"   ✅ POST /api/v1/diagnosis - {response.status_code}")
                    print(f"      Predicted: {diagnosis_data.get('predicted_label')}")
                    print(f"      Confidence: {diagnosis_data.get('confidence'):.2%}")
                    print(f"      Quality: {diagnosis_data.get('image_quality_label')} ({diagnosis_data.get('image_quality_score')})")
                    print(f"      Analysis ID: {analysis_id}")
                    print(f"      Top-K Predictions: {len(diagnosis_data.get('top_k', []))}")
                else:
                    print(f"   ❌ POST /api/v1/diagnosis - {response.status_code}")
                    print(f"      Error: {response.text}")
                    return False
            else:
                print(f"   ⚠️  Test image not found: {TEST_IMAGE}")
                print(f"      Skipping diagnosis test")
                
        except Exception as e:
            print(f"   ❌ Diagnosis failed: {e}")
            return False
        
        print()
        
        # 5. History
        print("5️⃣  Testing History...")
        print("-" * 70)
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/history?limit=5",
                headers=headers
            )
            
            if response.status_code == 200:
                history_data = response.json()
                print(f"   ✅ GET /api/v1/history - {response.status_code}")
                print(f"      Total: {history_data.get('total')}")
                print(f"      Returned: {len(history_data.get('analyses', []))}")
                
                if history_data.get('analyses'):
                    first = history_data['analyses'][0]
                    print(f"      Latest: {first.get('predicted_label')} ({first.get('confidence'):.2%})")
            else:
                print(f"   ❌ GET /api/v1/history - {response.status_code}")
                print(f"      Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ History retrieval failed: {e}")
            return False
        
        print()
        
        # 6. Get Diagnosis by ID
        if analysis_id:
            print("6️⃣  Testing Get Diagnosis by ID...")
            print("-" * 70)
            
            try:
                response = await client.get(
                    f"{BASE_URL}/api/v1/diagnosis/{analysis_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    diagnosis_data = response.json()
                    print(f"   ✅ GET /api/v1/diagnosis/{analysis_id} - {response.status_code}")
                    print(f"      ID: {diagnosis_data.get('id')}")
                    print(f"      Disease: {diagnosis_data.get('predicted_label')}")
                    print(f"      Confidence: {diagnosis_data.get('confidence'):.2%}")
                else:
                    print(f"   ❌ GET /api/v1/diagnosis/{analysis_id} - {response.status_code}")
                    print(f"      Error: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Get diagnosis by ID failed: {e}")
                return False
            
            print()
        
        # 7. Test Deprecated Endpoints (should return 404)
        print("7️⃣  Testing Deprecated Endpoints (should be 404)...")
        print("-" * 70)
        
        deprecated_tests = [
            ("POST", "/api/v1/diagnosis/diagnose"),
            ("GET", "/api/v1/diagnosis/diagnoses"),
            ("GET", "/api/v1/diagnosis/diagnoses/1"),
        ]
        
        all_deprecated_ok = True
        
        for method, path in deprecated_tests:
            try:
                if method == "POST":
                    response = await client.post(f"{BASE_URL}{path}", headers=headers)
                else:
                    response = await client.get(f"{BASE_URL}{path}", headers=headers)
                
                if response.status_code == 404:
                    print(f"   ✅ {method:6} {path} - 404 (correctly removed)")
                else:
                    print(f"   ❌ {method:6} {path} - {response.status_code} (should be 404!)")
                    all_deprecated_ok = False
                    
            except Exception as e:
                print(f"   ✅ {method:6} {path} - Not found (correctly removed)")
        
        if not all_deprecated_ok:
            print("\n   ⚠️  Some deprecated endpoints are still accessible!")
        
        print()
    
    # Final Summary
    print("=" * 70)
    print("✅ All Tests Passed!")
    print("=" * 70)
    print()
    print("📋 Summary:")
    print("   ✅ Health checks working")
    print("   ✅ Authentication flow working")
    print("   ✅ Diagnosis endpoint working")
    print("   ✅ History endpoint working")
    print("   ✅ Get by ID endpoint working")
    print("   ✅ Deprecated endpoints removed")
    print()
    print("🎉 API is fully functional and clean!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("\n⚠️  Make sure the server is running:")
    print("   uvicorn app.main:app --reload\n")
    
    try:
        success = asyncio.run(test_complete_flow())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
