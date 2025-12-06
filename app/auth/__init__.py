"""
Auth module initialization
"""
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token, decode_access_token
from app.auth.dependencies import get_current_user, get_optional_user, get_current_user_or_create_anonymous

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "get_optional_user",
    "get_current_user_or_create_anonymous",
]
