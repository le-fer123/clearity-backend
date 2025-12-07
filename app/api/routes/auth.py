import logging
from urllib.parse import urlencode
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Depends
from starlette.requests import Request

from app.config import settings
from app.auth.jwt_handler import create_access_token
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.repositories.session_repository import session_repository
from app.rate_limit import limiter

from uuid import UUID

from app.models.auth import RegisterRequest, LoginRequest, AuthResponse, UserInfoResponse
from app.repositories.session_repository import session_repository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/auth/google/login")
async def google_login():
    """Return a Google OAuth 2.0 authorization URL to start sign-in/up."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth client not configured")

    params = {
        "response_type": "code",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return {"auth_url": auth_url}


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: Optional[str] = None):
    """Handle Google OAuth callback: exchange code, get userinfo, sign in/up and return JWT."""
    if code is None:
        raise HTTPException(status_code=400, detail="Missing code")

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth client not configured")

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        try:
            token_resp = await client.post(token_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
            token_resp.raise_for_status()
            token_json = token_resp.json()
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            raise HTTPException(status_code=502, detail="Failed to exchange code for token")

        access_token = token_json.get("access_token")
        if not access_token:
            logger.error(f"Token response missing access_token: {token_json}")
            raise HTTPException(status_code=502, detail="Invalid token response")

        # Fetch userinfo
        try:
            userinfo_resp = await client.get("https://openidconnect.googleapis.com/v1/userinfo", headers={"Authorization": f"Bearer {access_token}"})
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch userinfo: {e}")
            raise HTTPException(status_code=502, detail="Failed to fetch userinfo")

    email = userinfo.get("email")
    email_verified = bool(userinfo.get("email_verified"))
    provider = "google"
    provider_user_id = userinfo.get("sub")

    if not email or not provider_user_id:
        raise HTTPException(status_code=502, detail="Incomplete userinfo from provider")

    # If an oauth_account exists, sign in that user
    account = await session_repository.get_oauth_account(provider, provider_user_id)
    if account:
        user_id = account["user_id"]
        await session_repository.update_last_login(user_id)
        token = create_access_token(user_id)
        return {"access_token": token, "token_type": "bearer", "user_id": str(user_id)}
    
    # Check for existing user by email
    existing = await session_repository.get_user_by_email(email)
    if existing:
        user_id = existing["id"]
        # Link oauth account
        await session_repository.create_oauth_account(user_id, provider, provider_user_id, provider_data=userinfo)
        await session_repository.update_last_login(user_id)
        token = create_access_token(user_id)
        return {"access_token": token, "token_type": "bearer", "user_id": str(user_id)}

    # Create new user (OAuth)
    user_id = await session_repository.create_user_oauth(email=email, email_verified=email_verified)
    await session_repository.create_oauth_account(user_id, provider, provider_user_id, provider_data=userinfo)
    await session_repository.update_last_login(user_id)

    token = create_access_token(user_id)
    return {"access_token": token, "token_type": "bearer", "user_id": str(user_id)}



@router.post("/auth/register", response_model=AuthResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    try:
        existing_user = await session_repository.get_user_by_email(body.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        password_hash = hash_password(body.password)
        user_id = await session_repository.create_user(body.email, password_hash)

        await session_repository.update_last_login(user_id)

        access_token = create_access_token(user_id)
        
        logger.info(f"User registered successfully: {body.email}")
        
        return AuthResponse(
            access_token=access_token,
            user_id=user_id,
            email=body.email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/auth/login", response_model=AuthResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    try:
        user = await session_repository.get_user_by_email(body.email)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        if not verify_password(body.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        await session_repository.update_last_login(user["id"])
        
        access_token = create_access_token(user["id"])
        
        logger.info(f"User logged in: {body.email}")
        
        return AuthResponse(
            access_token=access_token,
            user_id=user["id"],
            email=user["email"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/auth/me", response_model=UserInfoResponse)
@limiter.limit("5/minute")
async def get_current_user_info(request: Request, user_id: UUID = Depends(get_current_user)):
    try:
        user = await session_repository.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserInfoResponse(
            user_id=user["id"],
            email=user.get("email"),
            is_anonymous=user["is_anonymous"],
            email_verified=user.get("email_verified", False),
            created_at=user["created_at"],
            last_login=user.get("last_login")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch user info")
