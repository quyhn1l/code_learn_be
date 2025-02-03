# app/core/dependencies.py
from fastapi import Depends, HTTPException, status
from typing import List, Optional

from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from app.models import User
from app.core.constants import UserRole
from app.core.security import ALGORITHM, SECRET_KEY, oauth2_scheme, verify_token
from database import get_db
from jose import JWTError, jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current user info from JWT token
    """
    token_data = verify_token(token)
    # Tạo user object từ token data
    return User(
        id=token_data["id"],
        email=token_data["email"], 
        role=token_data["role"],
        is_active=True 
    )

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False  # Không báo lỗi khi không có token
)

async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    if not token:
        return None
    
    token_data = verify_token(token, required=False)
    if not token_data:
        return None
        
    return User(
        id=token_data["id"],
        email=token_data["email"],
        role=token_data["role"],
        is_active=True
    )


def check_roles(allowed_roles: List[str]):
    """
    Check if current user has required role
    """
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to perform this action"
            )
        return current_user
    return role_checker