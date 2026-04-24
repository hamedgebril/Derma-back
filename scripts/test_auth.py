"""
Test authentication endpoints
Quick script to verify signup/login functionality
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_auth():
    """Test authentication flow"""
    from app.infrastructure.database.session import get_async_session
    from app.infrastructure.database.repositories.user_repository import UserRepository
    from app.core.security import verify_password, create_access_token, decode_access_token
    
    print("=" * 60)
    print("Testing Authentication System")
    print("=" * 60)
    
    # Test 1: Create user
    print("\n1. Testing user creation...")
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        
        # Check if test user exists
        existing = await user_repo.get_by_email("test@example.com")
        if existing:
            print("  ℹ️  Test user already exists, skipping creation")
            user = existing
        else:
            from app.core.security import get_password_hash
            hashed_pw = get_password_hash("test123")
            user = await user_repo.create(
                email="test@example.com",
                username="testuser",
                hashed_password=hashed_pw
            )
            print(f"  ✅ User created: ID={user.id}, Email={user.email}")
    
    # Test 2: Verify password
    print("\n2. Testing password verification...")
    correct = verify_password("test123", user.hashed_password)
    wrong = verify_password("wrongpass", user.hashed_password)
    
    if correct and not wrong:
        print("  ✅ Password verification works correctly")
    else:
        print("  ❌ Password verification failed")
        return False
    
    # Test 3: Create JWT token
    print("\n3. Testing JWT token creation...")
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    print(f"  ✅ Token created: {token[:50]}...")
    
    # Test 4: Decode JWT token
    print("\n4. Testing JWT token decoding...")
    payload = decode_access_token(token)
    
    if payload and payload.get("sub") == str(user.id):
        print(f"  ✅ Token decoded successfully")
        print(f"     User ID: {payload.get('sub')}")
        print(f"     Email: {payload.get('email')}")
    else:
        print("  ❌ Token decoding failed")
        return False
    
    # Test 5: Verify user lookup
    print("\n5. Testing user lookup...")
    async with get_async_session() as session:
        user_repo = UserRepository(session)
        
        found_by_id = await user_repo.get_by_id(user.id)
        found_by_email = await user_repo.get_by_email(user.email)
        found_by_username = await user_repo.get_by_username(user.username)
        
        if found_by_id and found_by_email and found_by_username:
            print("  ✅ User lookup works (by ID, email, username)")
        else:
            print("  ❌ User lookup failed")
            return False
    
    print("\n" + "=" * 60)
    print("✅ All authentication tests passed!")
    print("=" * 60)
    print("\nYou can now test the API endpoints:")
    print(f"  Email: {user.email}")
    print(f"  Password: test123")
    print(f"  Token: {token[:50]}...")
    print("\nExample curl commands:")
    print(f'\ncurl -X POST "http://localhost:8000/api/v1/auth/login" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"email":"{user.email}","password":"test123"}}\'')
    print(f'\ncurl -X POST "http://localhost:8000/api/v1/diagnosis" \\')
    print(f'  -H "Authorization: Bearer {token[:50]}..." \\')
    print(f'  -F "file=@test_image.jpg"')
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_auth())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
