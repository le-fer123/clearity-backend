"""
Quick API test script
Run this after starting the server to test basic functionality
"""

import asyncio

import httpx

BASE_URL = "http://127.0.0.1:8000"


async def test_api():
    async with httpx.AsyncClient(timeout=3600.0) as client:
        print("=== Testing Clearity API ===\n")

        print("1. Health Check...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}\n")

        print("2. Creating Session...")
        response = await client.post(f"{BASE_URL}/api/sessions", json={})
        print(f"   Status Code: {response.status_code}")
        session_data = response.json()
        print(f"   Response Data: {session_data}")
        
        # Handle both possible response formats
        session_id = session_data.get("session_id") or session_data.get("id")
        user_id = session_data.get("user_id")
        
        if not session_id:
            print(f"   ERROR: Could not find session_id in response: {session_data}")
            return
        
        print(f"   Session ID: {session_id}")
        print(f"   User ID: {user_id}\n")

        print("3. Sending First Message...")
        message_data = {
            "session_id": session_id,
            "message": "I'm feeling really overwhelmed. I have three startup ideas I'm working on - Clearity, Re-skill, and a Dental CRM. I don't know which one to focus on and I feel stuck."
        }
        response = await client.post(f"{BASE_URL}/api/chat", json=message_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ERROR: {response.text}")
            return
            
        chat_response = response.json()
        print(f"   Response keys: {chat_response.keys()}")
        
        # Safely access message
        if "message" in chat_response:
            msg = chat_response['message']
            print(f"   Assistant: {msg[:200] if len(msg) > 200 else msg}...\n")
        else:
            print(f"   WARNING: No 'message' in response. Full response: {chat_response}\n")

        if chat_response.get("mind_map"):
            print(f"   Mind Map: {chat_response['mind_map'].get('map_name', 'N/A')}")
            print(f"   Theme: {chat_response['mind_map'].get('central_theme', 'N/A')}")
            print(f"   Projects: {len(chat_response['mind_map'].get('projects', []))}\n")

        if chat_response.get("suggested_tasks"):
            print(f"   Suggested Tasks: {len(chat_response['suggested_tasks'])}")
            for i, task in enumerate(chat_response['suggested_tasks'][:2], 1):
                print(f"   {i}. {task.get('name', 'N/A')}")
                print(f"      Priority: {task.get('priority_score', 0):.2f}")
                print(f"      KPI: {task.get('kpi', 'N/A')}")
            print()

        print("4. Getting Mind Map...")
        response = await client.get(f"{BASE_URL}/api/sessions/{session_id}/mindmap")
        if response.status_code == 200:
            mind_map = response.json()
            print(f"   Map Name: {mind_map.get('map_name', 'N/A')}")
            print(f"   Projects: {len(mind_map.get('projects', []))}")
            print(f"   Connections: {len(mind_map.get('connections', []))}\n")
        else:
            print(f"   ERROR: {response.status_code} - {response.text}\n")

        print("5. Getting Tasks...")
        response = await client.get(f"{BASE_URL}/api/sessions/{session_id}/tasks")
        if response.status_code == 200:
            tasks = response.json()
            print(f"   Total Tasks: {len(tasks)}")
            for i, task in enumerate(tasks[:3], 1):
                print(f"   {i}. {task.get('name', 'N/A')} (priority: {task.get('priority_score', 0):.2f})")
            print()
        else:
            print(f"   ERROR: {response.status_code} - {response.text}\n")

        print("6. Sending Follow-up Message...")
        message_data = {
            "session_id": session_id,
            "message": "I think Clearity feels most aligned with who I am, but I'm worried about market validation."
        }
        response = await client.post(f"{BASE_URL}/api/chat", json=message_data)
        if response.status_code == 200:
            chat_response = response.json()
            if "message" in chat_response:
                msg = chat_response['message']
                print(f"   Assistant: {msg[:200] if len(msg) > 200 else msg}...\n")
            else:
                print(f"   No message in response\n")
        else:
            print(f"   ERROR: {response.status_code} - {response.text}\n")

        print("7. Getting User Snapshots...")
        response = await client.get(f"{BASE_URL}/api/users/{user_id}/snapshots")
        if response.status_code == 200:
            snapshots = response.json()
            print(f"   Snapshots Found: {len(snapshots)}")
            for snapshot in snapshots:
                print(f"   - {snapshot.get('map_name', 'N/A')}")
                print(f"     Unresolved: {len(snapshot.get('unresolved_issues', []))} issues")
            print()
        else:
            print(f"   ERROR: {response.status_code} - {response.text}\n")

        print("=== Test Complete ===")
        print(f"\nSession ID: {session_id}")
        print(f"User ID: {user_id}")
        print(f"\nAPI Docs: {BASE_URL}/docs")


if __name__ == "__main__":
    asyncio.run(test_api())
