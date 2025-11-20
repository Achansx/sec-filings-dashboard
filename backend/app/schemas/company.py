"""Pydantic schemas for Company model."""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class CompanyBase(BaseModel):
    """Base schema for Company with common attributes."""

    cik: str = Field(..., max_length=10, description="Central Index Key")
    name: str = Field(..., description="Company name")
    ticker: Optional[str] = Field(None, max_length=10, description="Stock ticker symbol")
    sic_code: Optional[str] = Field(None, max_length=4, description="Standard Industrial Classification code")
    industry_description: Optional[str] = Field(None, description="Industry description")
    fiscal_year_end: Optional[str] = Field(None, max_length=4, description="Fiscal year end (MMDD format)")
    state_of_incorporation: Optional[str] = Field(None, max_length=2, description="State of incorporation")
    # Note: Named extra_metadata to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON")


class CompanyCreate(CompanyBase):
    """Schema for creating a new Company."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating a Company."""

    name: Optional[str] = None
    ticker: Optional[str] = Field(None, max_length=10)
    sic_code: Optional[str] = Field(None, max_length=4)
    industry_description: Optional[str] = None
    fiscal_year_end: Optional[str] = Field(None, max_length=4)
    state_of_incorporation: Optional[str] = Field(None, max_length=2)
    # Note: Named extra_metadata to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    extra_metadata: Optional[Dict[str, Any]] = None


class CompanyInDB(CompanyBase):
    """Schema for Company as stored in database."""

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Company(CompanyInDB):
    """Schema for Company returned by API."""
    pass


class CompanyWithFilingsCount(Company):
    """Schema for Company with filing count."""

    filings_count: int = Field(0, description="Number of filings for this company")
