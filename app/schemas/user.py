from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    username: str
    role: str = "student"  

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime 
    updated_at: datetime

class LoginSchema(BaseModel):
    email: str
    password: str

class TokenUserResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool = True
    
    class Config:
        from_attributes = True
