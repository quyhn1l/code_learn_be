# app/core/security.py
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.models import User

# JWT Configuration
SECRET_KEY = "2yxsxxc_n#b1xt8kanxtz=i*vy)e(dzohhmbi48aamn6r6^_c("
ALGORITHM = "HS256" 
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for Swagger UI - required auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# OAuth2 scheme for optional auth
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    auto_error=False
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(user: User):
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user.email,      # email trong sub (chuẩn JWT)
        "id": user.id,          # id của user
        "email": user.email,    # thêm email
        "username": user.username,  # thêm username
        "role": user.role,      # role của user
        "exp": expire           # thời gian hết hạn
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        SECRET_KEY, 
        algorithm=ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, required: bool = True):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if not all([email, user_id, username, role]):
            if required:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            return None
            
        return {
            "email": email,
            "id": user_id,
            "username": username,
            "role": role
        }
    except JWTError:
        if required:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return None