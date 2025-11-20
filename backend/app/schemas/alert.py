"""Pydantic schemas for UserAlert and AlertMatch models."""
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# UserAlert schemas
class UserAlertBase(BaseModel):
    """Base schema for UserAlert with common attributes."""

    name: str = Field(..., max_length=255, description="Alert name/description")
    conditions: Dict[str, Any] = Field(..., description="Alert conditions as JSON (company_cik, form_types, keywords, etc.)")
    notification_method: Optional[str] = Field(None, max_length=20, description="Notification method (email, webhook, etc.)")
    frequency: Optional[str] = Field(None, max_length=20, description="Notification frequency (immediate, daily, weekly)")
    is_active: bool = Field(True, description="Whether alert is active")


class UserAlertCreate(UserAlertBase):
    """Schema for creating a new UserAlert."""
    pass


class UserAlertUpdate(BaseModel):
    """Schema for updating a UserAlert."""

    name: Optional[str] = Field(None, max_length=255)
    conditions: Optional[Dict[str, Any]] = None
    notification_method: Optional[str] = Field(None, max_length=20)
    frequency: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class UserAlertInDB(UserAlertBase):
    """Schema for UserAlert as stored in database."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserAlert(UserAlertInDB):
    """Schema for UserAlert returned by API."""
    pass


class UserAlertWithMatches(UserAlert):
    """Schema for UserAlert with match count."""

    matches_count: int = Field(0, description="Number of matches for this alert")


# AlertMatch schemas
class AlertMatchBase(BaseModel):
    """Base schema for AlertMatch with common attributes."""

    alert_id: UUID = Field(..., description="Reference to alert that matched")
    filing_id: int = Field(..., description="Reference to filing that matched")
    notification_status: Optional[str] = Field(None, max_length=20, description="Notification status (pending, sent, failed)")


class AlertMatchCreate(AlertMatchBase):
    """Schema for creating a new AlertMatch."""
    pass


class AlertMatchUpdate(BaseModel):
    """Schema for updating an AlertMatch."""

    notified_at: Optional[datetime] = None
    notification_status: Optional[str] = Field(None, max_length=20)


class AlertMatchInDB(AlertMatchBase):
    """Schema for AlertMatch as stored in database."""

    id: int
    matched_at: datetime
    notified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AlertMatch(AlertMatchInDB):
    """Schema for AlertMatch returned by API."""
    pass


class AlertMatchWithDetails(AlertMatch):
    """Schema for AlertMatch with alert and filing details."""

    alert_name: Optional[str] = Field(None, description="Name of the alert")
    filing_form_type: Optional[str] = Field(None, description="Form type of the filing")
    filing_company_cik: Optional[str] = Field(None, description="Company CIK of the filing")
    company_name: Optional[str] = Field(None, description="Company name")
