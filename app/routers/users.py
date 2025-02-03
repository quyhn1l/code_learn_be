from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from database import get_db
from app.models import User
from app.schemas.user import UserCreate, UserResponse 

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    existing_user = db.execute(
        select(User).where(User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(400, "Email already registered")
    
    new_user = User(
        email=user.email,
        username=user.username,
        password_hash=user.password,  # Remember to hash in production
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/", response_model=List[UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    users = db.execute(
        select(User).offset(skip).limit(limit)
    ).scalars().all()
    
    return users