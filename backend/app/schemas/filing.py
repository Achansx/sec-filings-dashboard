"""Pydantic schemas for Filing and FilingDocument models."""
from datetime import datetime, date
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


# FilingDocument schemas
class FilingDocumentBase(BaseModel):
    """Base schema for FilingDocument with common attributes."""

    document_type: Optional[str] = Field(None, max_length=20, description="Type of document")
    sequence: Optional[int] = Field(None, description="Sequence number within filing")
    description: Optional[str] = Field(None, description="Document description")
    url: Optional[str] = Field(None, description="URL to document on SEC EDGAR")
    size_bytes: Optional[int] = Field(None, description="Document size in bytes")


class FilingDocumentCreate(FilingDocumentBase):
    """Schema for creating a new FilingDocument."""
    filing_id: int = Field(..., description="Reference to parent filing")


class FilingDocumentInDB(FilingDocumentBase):
    """Schema for FilingDocument as stored in database."""

    id: int
    filing_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilingDocument(FilingDocumentInDB):
    """Schema for FilingDocument returned by API."""
    pass


# Filing schemas
class FilingBase(BaseModel):
    """Base schema for Filing with common attributes."""

    accession_number: str = Field(..., max_length=20, description="SEC accession number (unique identifier)")
    company_cik: str = Field(..., max_length=10, description="Reference to company CIK")
    form_type: str = Field(..., max_length=10, description="Form type (e.g., 10-K, 10-Q)")
    filing_date: date = Field(..., description="Date filing was submitted")
    period_of_report: Optional[date] = Field(None, description="Period end date covered by report")
    accepted_datetime: Optional[datetime] = Field(None, description="Date and time SEC accepted the filing")
    description: Optional[str] = Field(None, description="Filing description")
    document_count: Optional[int] = Field(None, description="Number of documents in filing")
    file_url: Optional[str] = Field(None, description="URL to filing on SEC EDGAR")
    indexed: bool = Field(False, description="Whether filing has been indexed in Elasticsearch")
    # Note: Named extra_metadata to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata as JSON")


class FilingCreate(FilingBase):
    """Schema for creating a new Filing."""
    pass


class FilingUpdate(BaseModel):
    """Schema for updating a Filing."""

    form_type: Optional[str] = Field(None, max_length=10)
    filing_date: Optional[date] = None
    period_of_report: Optional[date] = None
    accepted_datetime: Optional[datetime] = None
    description: Optional[str] = None
    document_count: Optional[int] = None
    file_url: Optional[str] = None
    indexed: Optional[bool] = None
    # Note: Named extra_metadata to avoid conflict with SQLAlchemy's reserved 'metadata' attribute
    extra_metadata: Optional[Dict[str, Any]] = None


class FilingInDB(FilingBase):
    """Schema for Filing as stored in database."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Filing(FilingInDB):
    """Schema for Filing returned by API."""
    pass


class FilingWithCompany(Filing):
    """Schema for Filing with company information."""

    company_name: Optional[str] = Field(None, description="Company name")
    company_ticker: Optional[str] = Field(None, description="Company ticker")


class FilingWithDocuments(Filing):
    """Schema for Filing with associated documents."""

    documents: List[FilingDocument] = Field(default_factory=list, description="Filing documents")


class FilingDetail(FilingWithCompany):
    """Schema for detailed Filing with company info and documents."""

    documents: List[FilingDocument] = Field(default_factory=list, description="Filing documents")
