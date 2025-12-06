"""
Database utility script for common operations
"""

import asyncio
import os
import sys

import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def check_connection():
    """Check database connection"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        version = await conn.fetchval("SELECT version()")
        print(f"✓ Connected to PostgreSQL")
        print(f"  Version: {version.split(',')[0]}")
        await conn.close()
        return True
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        return False


async def check_tables():
    """Check if all required tables exist"""
    tables = [
        "users", "sessions", "mind_maps", "fields", "projects",
        "project_fields", "connections", "issues", "issue_projects",
        "root_causes", "root_cause_issues", "plans", "tasks",
        "task_projects", "snapshots", "messages"
    ]

    conn = await asyncpg.connect(DATABASE_URL)

    print("\nChecking tables:")
    all_exist = True
    for table in tables:
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            table
        )
        status = "✓" if exists else "✗"
        print(f"  {status} {table}")
        if not exists:
            all_exist = False

    await conn.close()
    return all_exist


async def show_stats():
    """Show database statistics"""
    conn = await asyncpg.connect(DATABASE_URL)

    print("\nDatabase Statistics:")

    users_count = await conn.fetchval("SELECT COUNT(*) FROM users")
    print(f"  Users: {users_count}")

    sessions_count = await conn.fetchval("SELECT COUNT(*) FROM sessions")
    print(f"  Sessions: {sessions_count}")

    mind_maps_count = await conn.fetchval("SELECT COUNT(*) FROM mind_maps")
    print(f"  Mind Maps: {mind_maps_count}")

    projects_count = await conn.fetchval("SELECT COUNT(*) FROM projects")
    print(f"  Projects: {projects_count}")

    tasks_count = await conn.fetchval("SELECT COUNT(*) FROM tasks")
    print(f"  Tasks: {tasks_count}")

    messages_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
    print(f"  Messages: {messages_count}")

    snapshots_count = await conn.fetchval("SELECT COUNT(*) FROM snapshots")
    print(f"  Snapshots: {snapshots_count}")

    await conn.close()


async def reset_database():
    """Reset database (DANGER: deletes all data)"""
    response = input("⚠️  This will DELETE ALL DATA. Are you sure? (type 'yes' to confirm): ")

    if response.lower() != "yes":
        print("Cancelled.")
        return

    conn = await asyncpg.connect(DATABASE_URL)

    print("\nResetting database...")

    await conn.execute(
        "TRUNCATE users, sessions, mind_maps, projects, connections, issues, root_causes, plans, tasks, snapshots, messages CASCADE")

    print("✓ All data deleted")

    await conn.close()


async def init_database():
    """Initialize database with schema"""
    print("Initializing database schema...")

    conn = await asyncpg.connect(DATABASE_URL)

    schema_path = "app/schemas/db_schema.sql"

    if not os.path.exists(schema_path):
        print(f"✗ Schema file not found: {schema_path}")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()

    await conn.execute(schema)

    print("✓ Schema initialized")

    await conn.close()


async def main():
    if len(sys.argv) < 2:
        print("Database Utility")
        print("\nUsage:")
        print("  python db_utils.py check       - Check connection and tables")
        print("  python db_utils.py stats       - Show database statistics")
        print("  python db_utils.py init        - Initialize database schema")
        print("  python db_utils.py reset       - Reset database (DELETE ALL DATA)")
        return

    command = sys.argv[1]

    if command == "check":
        connected = await check_connection()
        if connected:
            await check_tables()

    elif command == "stats":
        await show_stats()

    elif command == "init":
        await init_database()
        await check_tables()

    elif command == "reset":
        await reset_database()

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
