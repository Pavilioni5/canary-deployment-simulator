"""
Authentication and Authorization REST Endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserProfileResponse
)
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User Account",
    description="Creates a new user with bcrypt-hashed password and assigned role (USER or ADMIN)."
)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    # Check if email is already taken
    existing = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    
    role = request.role.upper().strip() if request.role else "USER"
    if role not in ["ADMIN", "USER"]:
        role = "USER"

    user = User(
        email=request.email.lower().strip(),
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login & JWT Generation",
    description="Authenticates credentials and returns a signed JSON Web Token (JWT)."
)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email.lower().strip()).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    # Issue JWT token
    token_claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    }
    access_token = create_access_token(data=token_claims)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Current Authenticated User Profile",
    description="Returns the profile and role of the currently authenticated user using Bearer JWT token."
)
def get_profile(current_user: User = Depends(get_current_user)):
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.get(
    "/admin-only",
    status_code=status.HTTP_200_OK,
    summary="RBAC Protected Route Demo",
    description="Demonstrates Role-Based Access Control (RBAC). Only accessible by users with role=ADMIN."
)
def admin_only_check(current_user: User = Depends(require_admin)):
    return {
        "message": "Access granted to admin-only area.",
        "admin_email": current_user.email,
        "role": current_user.role
    }
