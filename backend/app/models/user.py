"""Pydantic models for user management"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """User model"""
    user_id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    language_preference: str = "en"
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "email": "user@example.com",
                "name": "John Doe",
                "phone": "+911234567890",
                "language_preference": "en",
                "created_at": "2025-10-17T10:00:00Z"
            }
        }


class UserProfile(BaseModel):
    """User profile with additional information"""
    user_id: str
    email: EmailStr
    name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    language_preference: str = "en"
    total_documents: int = 0
    total_conversations: int = 0
    total_prescriptions: int = 0
    last_login: Optional[datetime] = None
    member_since: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "email": "user@example.com",
                "name": "John Doe",
                "total_documents": 5,
                "total_conversations": 12,
                "total_prescriptions": 3,
                "member_since": "2025-01-01T00:00:00Z"
            }
        }


class UserCreate(BaseModel):
    """User creation request"""
    email: EmailStr
    name: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    language_preference: str = "en"
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update request"""
    name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    language_preference: Optional[str] = None


# Alias for backwards compatibility
UserProfileUpdate = UserUpdate


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    """User login response with JWT token"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User

