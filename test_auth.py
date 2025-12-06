"""
Authentication API test script
Test the simplified JWT authentication flows
"""

import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000"


async def test_auth():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("=== Testing Clearity Authentication ===\n")
        
        # Test 1: Anonymous user flow (no JWT)
        print("1. Testing Anonymous User Flow (No JWT)...")
        response = await client.post(f"{BASE_URL}/api/chat", json={
            "message": "I'm feeling overwhelmed with work"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            session_id = data["session_id"]
            print(f"   ✓ Created anonymous session: {session_id}")
            print(f"   User stays anonymous - no JWT needed\n")
        else:
            print(f"   ERROR: {response.text}\n")
            return
        
        # Test 2: Continue anonymous session
        print("2. Testing Anonymous Session Continuation...")
        response = await client.post(f"{BASE_URL}/api/chat", json={
            "session_id": session_id,
            "message": "What should I do?"
        })
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Continued anonymous session without JWT\n")
        else:
            print(f"   ERROR: {response.text}\n")
        
        # Test 3: Register new user
        print("3. Testing User Registration...")
        test_email = "test@clearity.app"
        test_password = "SecurePassword123"
        
        response = await client.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password
        })
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            auth_data = response.json()
            access_token = auth_data["access_token"]
            user_id = auth_data["user_id"]
            print(f"   User ID: {user_id}")
            print(f"   Token: {access_token[:20]}...")
            print(f"   ✓ Registration successful\n")
        else:
            print(f"   Note: {response.json().get('detail', 'Unknown error')}")
            print(f"   (User may already exist - trying login...)\n")
            
            # Try login instead
            print("3b. Logging in with existing credentials...")
            response = await client.post(f"{BASE_URL}/api/auth/login", json={
                "email": test_email,
                "password": test_password
            })
            if response.status_code == 200:
                auth_data = response.json()
                access_token = auth_data["access_token"]
                user_id = auth_data["user_id"]
                print(f"   ✓ Login successful\n")
            else:
                print(f"   ERROR: {response.text}\n")
                return
        
        # Test 4: Get user info with JWT
        print("4. Testing JWT Authentication...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{BASE_URL}/api/auth/me", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   Email: {user_info.get('email')}")
            print(f"   Is Anonymous: {user_info.get('is_anonymous')}")
            print(f"   ✓ JWT validation successful\n")
        else:
            print(f"   ERROR: {response.text}\n")
        
        # Test 5: Send message with JWT (authenticated)
        print("5. Testing Authenticated Chat with JWT...")
        response = await client.post(
            f"{BASE_URL}/api/chat",
            headers=headers,
            json={"message": "Now I'm logged in!"}
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Session ID: {data['session_id']}")
            print(f"   Message: {data['message'][:100]}...")
            print(f"   ✓ Authenticated chat successful\n")
        else:
            print(f"   ERROR: {response.text}\n")
        
        print("=== Simplified Authentication Flow ===")
        print("Anonymous: Just don't send JWT, use session_id")
        print("Registered: /register → JWT → Use in Authorization header")
        print("=========================================")


if __name__ == "__main__":
    asyncio.run(test_auth())
