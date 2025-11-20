"""Filing models for SEC filings and associated documents."""
from sqlalchemy import (
    Column, String, Text, Date, TIMESTAMP, Integer, Boolean,
    ForeignKey, BigInteger, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Filing(Base):
    """
    Model for SEC filings.

    Stores information about individual SEC filings (10-K, 10-Q, 8-K, etc.)
    submitted by companies.
    """

    __tablename__ = "filings"

    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True, comment="Auto-incrementing ID")

    # Unique identifiers
    accession_number = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="SEC accession number (unique identifier)"
    )

    # Company relationship
    company_cik = Column(
        String(10),
        ForeignKey("companies.cik", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to company CIK"
    )

    # Filing Information
    form_type = Column(String(10), nullable=False, index=True, comment="Form type (e.g., 10-K, 10-Q)")
    filing_date = Column(Date, nullable=False, index=True, comment="Date filing was submitted")
    period_of_report = Column(Date, nullable=True, comment="Period end date covered by report")
    accepted_datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Date and time SEC accepted the filing"
    )
    description = Column(Text, nullable=True, comment="Filing description")
    document_count = Column(Integer, nullable=True, comment="Number of documents in filing")
    file_url = Column(Text, nullable=True, comment="URL to filing on SEC EDGAR")

    # Processing Status
    indexed = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether filing has been indexed in Elasticsearch"
    )

    # Metadata
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    # Note: Using 'extra_metadata' as attribute name because 'metadata' is reserved by SQLAlchemy
    extra_metadata = Column("metadata", JSONB, nullable=True, comment="Additional metadata as JSON")

    # Relationships
    company = relationship("Company", back_populates="filings")
    documents = relationship(
        "FilingDocument",
        back_populates="filing",
        cascade="all, delete-orphan"
    )
    alert_matches = relationship(
        "AlertMatch",
        back_populates="filing",
        cascade="all, delete-orphan"
    )

    # Indexes
    __table_args__ = (
        Index("idx_filings_company_date", "company_cik", "filing_date", postgresql_using="btree"),
        Index("idx_filings_form_date", "form_type", "filing_date", postgresql_using="btree"),
        Index("idx_filings_date_desc", filing_date.desc()),
        Index("idx_filings_not_indexed", "indexed", postgresql_where=(indexed == False)),
        {"comment": "SEC filings submitted by companies"}
    )

    def __repr__(self) -> str:
        """String representation of Filing."""
        return (
            f"<Filing(id={self.id}, accession={self.accession_number}, "
            f"form={self.form_type}, date={self.filing_date})>"
        )


class FilingDocument(Base):
    """
    Model for individual documents within a SEC filing.

    A single filing can contain multiple documents (e.g., main form, exhibits, etc.)
    """

    __tablename__ = "filing_documents"

    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True, comment="Auto-incrementing ID")

    # Filing relationship
    filing_id = Column(
        BigInteger,
        ForeignKey("filings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to parent filing"
    )

    # Document Information
    document_type = Column(String(20), nullable=True, comment="Type of document")
    sequence = Column(Integer, nullable=True, comment="Sequence number within filing")
    description = Column(Text, nullable=True, comment="Document description")
    url = Column(Text, nullable=True, comment="URL to document on SEC EDGAR")
    size_bytes = Column(BigInteger, nullable=True, comment="Document size in bytes")

    # Metadata
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )

    # Relationships
    filing = relationship("Filing", back_populates="documents")

    # Indexes
    __table_args__ = (
        Index("idx_filing_documents_filing", "filing_id"),
        {"comment": "Individual documents within SEC filings"}
    )

    def __repr__(self) -> str:
        """String representation of FilingDocument."""
        return (
            f"<FilingDocument(id={self.id}, filing_id={self.filing_id}, "
            f"type={self.document_type})>"
        )
