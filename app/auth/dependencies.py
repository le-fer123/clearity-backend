import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_handler import decode_access_token
from app.repositories.session_repository import session_repository

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UUID:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UUID]:
    if not credentials:
        return None
    
    token = credentials.credentials
    user_id = decode_access_token(token)
    
    if user_id is None:
        logger.warning("Invalid JWT token provided in optional auth")
        return None
    
    return user_id


async def get_current_user_or_create_anonymous(
    user_id: Optional[UUID] = Depends(get_optional_user)
) -> UUID:

    if user_id is not None:
        return user_id
    
    # Create anonymous user
    new_user_id = await session_repository.create_anonymous_user()
    logger.info(f"Created anonymous user {new_user_id}")
    
    return new_user_id
