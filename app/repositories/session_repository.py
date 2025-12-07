import json
import logging
from typing import Optional
from uuid import UUID

from app.database import db

logger = logging.getLogger(__name__)


class SessionRepository:
    async def create_session(self, user_id: Optional[UUID] = None) -> dict:
        if user_id is None:
            user_id = await db.fetchval("INSERT INTO users DEFAULT VALUES RETURNING id")
            logger.info(f"Created new user: {user_id}")

        session = await db.fetchrow(
            "INSERT INTO sessions (user_id) VALUES ($1) RETURNING id, user_id, created_at, updated_at",
            user_id
        )
        logger.info(f"Created session {session['id']} for user {user_id}")
        return dict(session)

    async def get_session(self, session_id: UUID) -> Optional[dict]:
        session = await db.fetchrow(
            "SELECT id, user_id, created_at, updated_at FROM sessions WHERE id = $1",
            session_id
        )
        return dict(session) if session else None

    async def update_session(self, session_id: UUID):
        await db.execute(
            "UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = $1",
            session_id
        )

    async def get_user_sessions(self, user_id: UUID, limit: int = 10):
        sessions = await db.fetch(
            "SELECT id, user_id, created_at, updated_at FROM sessions WHERE user_id = $1 ORDER BY updated_at DESC LIMIT $2",
            user_id, limit
        )
        return [dict(s) for s in sessions]
    
    async def create_anonymous_user(self) -> UUID:
        """Create a new anonymous user"""
        user_id = await db.fetchval(
            "INSERT INTO users (is_anonymous) VALUES (TRUE) RETURNING id"
        )
        logger.info(f"Created anonymous user: {user_id}")
        return user_id
    
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email address"""
        user = await db.fetchrow(
            """SELECT id, email, password_hash, is_anonymous, email_verified, 
               created_at, last_login 
               FROM users WHERE email = $1""",
            email
        )
        return dict(user) if user else None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID"""
        user = await db.fetchrow(
            """SELECT id, email, is_anonymous, email_verified, created_at, last_login 
               FROM users WHERE id = $1""",
            user_id
        )
        return dict(user) if user else None
    
    async def create_user(self, email: str, password_hash: str) -> UUID:
        """Create a new registered user"""
        user_id = await db.fetchval(
            """INSERT INTO users (email, password_hash, is_anonymous, email_verified)
               VALUES ($1, $2, FALSE, FALSE) RETURNING id""",
            email, password_hash
        )
        logger.info(f"Created registered user: {user_id} ({email})")
        return user_id

    async def create_user_oauth(self, email: str, email_verified: bool = True) -> UUID:
        """Create a new user registered via OAuth (no password)."""
        user_id = await db.fetchval(
            """INSERT INTO users (email, password_hash, is_anonymous, email_verified)
               VALUES ($1, NULL, FALSE, $2) RETURNING id""",
            email, email_verified
        )
        logger.info(f"Created OAuth user: {user_id} ({email})")
        return user_id
    
    async def claim_anonymous_user(self, user_id: UUID, email: str, password_hash: str) -> None:
        """Convert anonymous user to registered user"""
        await db.execute(
            """UPDATE users 
               SET email = $1, password_hash = $2, is_anonymous = FALSE 
               WHERE id = $3 AND is_anonymous = TRUE""",
            email, password_hash, user_id
        )
        logger.info(f"Claimed anonymous user {user_id} with email {email}")
    
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp"""
        await db.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
            user_id
        )

    async def create_oauth_account(self, user_id: UUID, provider: str, provider_user_id: str, provider_data: dict | None = None) -> UUID:
        """Link an OAuth provider account to a local user."""
        provider_data = json.dumps(provider_data) if provider_data else None
        logger.info(f"Linking OAuth account for user {user_id} provider={provider} provider_user_id={provider_user_id} provider_data={provider_data}")
        account_id = await db.fetchval(
            """INSERT INTO oauth_accounts (user_id, provider, provider_user_id, provider_data)
               VALUES ($1, $2, $3, $4) RETURNING id""",
            user_id, provider, provider_user_id, provider_data
        )
        logger.info(f"Created oauth account {account_id} for user {user_id} provider={provider}")
        return account_id

    async def get_oauth_account(self, provider: str, provider_user_id: str) -> Optional[dict]:
        account = await db.fetchrow(
            "SELECT id, user_id, provider, provider_user_id, provider_data FROM oauth_accounts WHERE provider = $1 AND provider_user_id = $2",
            provider, provider_user_id
        )
        return dict(account) if account else None


session_repository = SessionRepository()
