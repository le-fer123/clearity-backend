import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends

from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.models.auth import RegisterRequest, LoginRequest, AuthResponse, UserInfoResponse
from app.repositories.session_repository import session_repository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(request: RegisterRequest):
    try:
        existing_user = await session_repository.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        password_hash = hash_password(request.password)
        user_id = await session_repository.create_user(request.email, password_hash)

        await session_repository.update_last_login(user_id)

        access_token = create_access_token(user_id)
        
        logger.info(f"User registered successfully: {request.email}")
        
        return AuthResponse(
            access_token=access_token,
            user_id=user_id,
            email=request.email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    try:
        user = await session_repository.get_user_by_email(request.email)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        if not verify_password(request.password, user["password_hash"]):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        await session_repository.update_last_login(user["id"])
        
        access_token = create_access_token(user["id"])
        
        logger.info(f"User logged in: {request.email}")
        
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
async def get_current_user_info(user_id: UUID = Depends(get_current_user)):
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
