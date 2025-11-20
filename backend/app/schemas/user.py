"""Pydantic schemas for User model."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserBase(BaseModel):
    """Base schema for User with common attributes."""

    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, max_length=255, description="User full name")


class UserCreate(UserBase):
    """Schema for creating a new User."""

    oauth_provider: Optional[str] = Field(None, max_length=50, description="OAuth provider (google, github, etc.)")
    oauth_id: Optional[str] = Field(None, max_length=255, description="OAuth provider user ID")


class UserUpdate(BaseModel):
    """Schema for updating a User."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for User as stored in database."""

    id: UUID
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Schema for User returned by API."""
    pass


class UserProfile(User):
    """Schema for User profile with additional information."""

    alerts_count: int = Field(0, description="Number of active alerts")
