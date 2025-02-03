from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.constants import UserRole
from app.dependencies import get_current_user
from app.models import User
from app.schemas.user import LoginSchema, TokenUserResponse, UserCreate, UserResponse, UserUpdate
from app.core.security import (
    create_access_token, 
    get_password_hash, 
    verify_password,
)
from database import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.execute(
        select(User).where(User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate role
    if user_data.role not in UserRole.get_valid_roles():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
async def login(
    credentials: LoginSchema,
    db: Session = Depends(get_db)
):
    # Find user
    result = db.execute(
        select(User).where(User.email == credentials.email)
    ).first()
    user = result[0] if result else None

    # Verify password
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token
    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=TokenUserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Hash new password if provided
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    current_user.updated_at = datetime.now()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user