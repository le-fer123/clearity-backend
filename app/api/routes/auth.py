import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from starlette.requests import Request

from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.rate_limit import limiter
from app.models.auth import RegisterRequest, LoginRequest, AuthResponse, UserInfoResponse
from app.repositories.session_repository import session_repository

logger = logging.getLogger(__name__)
router = APIRouter()


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
