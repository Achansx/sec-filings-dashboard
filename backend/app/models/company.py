"""Company model for SEC registered companies."""
from sqlalchemy import Column, String, Text, TIMESTAMP, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Company(Base):
    """
    Model for SEC registered companies.

    Stores company information retrieved from SEC EDGAR database.
    Primary key is the CIK (Central Index Key).
    """

    __tablename__ = "companies"

    # Primary Key
    cik = Column(String(10), primary_key=True, index=True, comment="Central Index Key")

    # Company Information
    name = Column(Text, nullable=False, comment="Company name")
    ticker = Column(String(10), nullable=True, index=True, comment="Stock ticker symbol")
    sic_code = Column(String(4), nullable=True, index=True, comment="Standard Industrial Classification code")
    industry_description = Column(Text, nullable=True, comment="Industry description")
    fiscal_year_end = Column(String(4), nullable=True, comment="Fiscal year end (MMDD format)")
    state_of_incorporation = Column(String(2), nullable=True, comment="State of incorporation")

    # Metadata
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp"
    )
    # Note: Using 'extra_metadata' as attribute name because 'metadata' is reserved by SQLAlchemy
    extra_metadata = Column("metadata", JSONB, nullable=True, comment="Additional metadata as JSON")

    # Relationships
    filings = relationship("Filing", back_populates="company", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_companies_ticker", "ticker"),
        Index("idx_companies_sic", "sic_code"),
        {"comment": "SEC registered companies"}
    )

    def __repr__(self) -> str:
        """String representation of Company."""
        return f"<Company(cik={self.cik}, name={self.name}, ticker={self.ticker})>"
