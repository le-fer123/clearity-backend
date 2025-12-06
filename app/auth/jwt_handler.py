"""
JWT token handling utilities
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt

from app.config import settings

logger = logging.getLogger(__name__)


def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User UUID
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
    
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.debug(f"Created JWT token for user {user_id}, expires at {expire}")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[UUID]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        User UUID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            logger.warning("JWT token missing 'sub' claim")
            return None
        
        user_id = UUID(user_id_str)
        logger.debug(f"Decoded JWT token for user {user_id}")
        return user_id
        
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except ValueError as e:
        logger.warning(f"Invalid UUID in JWT token: {e}")
        return None
