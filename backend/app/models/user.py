"""User models for authentication and alerts."""
from sqlalchemy import (
    Column, String, Boolean, TIMESTAMP, ForeignKey, Index, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class User(Base):
    """
    Model for application users.

    Supports OAuth authentication and stores user profile information.
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique user identifier"
    )

    # Authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address"
    )
    oauth_provider = Column(String(50), nullable=True, comment="OAuth provider (google, github, etc.)")
    oauth_id = Column(String(255), nullable=True, comment="OAuth provider user ID")

    # Profile
    full_name = Column(String(255), nullable=True, comment="User full name")
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether user account is active")

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Account creation timestamp"
    )
    last_login_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Last login timestamp"
    )

    # Relationships
    alerts = relationship("UserAlert", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_oauth", "oauth_provider", "oauth_id"),
        {"comment": "Application users"}
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"


class UserAlert(Base):
    """
    Model for user-configured alerts.

    Users can create alerts based on specific conditions (company, form type, keywords, etc.)
    to be notified when matching filings are submitted.
    """

    __tablename__ = "user_alerts"

    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique alert identifier"
    )

    # User relationship
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to user who created alert"
    )

    # Alert Configuration
    name = Column(String(255), nullable=False, comment="Alert name/description")
    conditions = Column(
        JSONB,
        nullable=False,
        comment="Alert conditions as JSON (company_cik, form_types, keywords, etc.)"
    )
    notification_method = Column(
        String(20),
        nullable=True,
        comment="Notification method (email, webhook, etc.)"
    )
    frequency = Column(
        String(20),
        nullable=True,
        comment="Notification frequency (immediate, daily, weekly)"
    )
    is_active = Column(Boolean, default=True, nullable=False, comment="Whether alert is active")

    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Alert creation timestamp"
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Alert last update timestamp"
    )

    # Relationships
    user = relationship("User", back_populates="alerts")
    matches = relationship("AlertMatch", back_populates="alert", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_alerts_user_active", "user_id", "is_active"),
        {"comment": "User-configured filing alerts"}
    )

    def __repr__(self) -> str:
        """String representation of UserAlert."""
        return f"<UserAlert(id={self.id}, user_id={self.user_id}, name={self.name})>"


class AlertMatch(Base):
    """
    Model for alert matches.

    Records when a filing matches a user's alert criteria and tracks notification status.
    """

    __tablename__ = "alert_matches"

    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True, comment="Auto-incrementing ID")

    # Relationships
    alert_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to alert that matched"
    )
    filing_id = Column(
        BigInteger,
        ForeignKey("filings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to filing that matched"
    )

    # Match Information
    matched_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When the match was detected"
    )
    notified_at = Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When user was notified"
    )
    notification_status = Column(
        String(20),
        nullable=True,
        comment="Notification status (pending, sent, failed)"
    )

    # Relationships
    alert = relationship("UserAlert", back_populates="matches")
    filing = relationship("Filing", back_populates="alert_matches")

    # Indexes
    __table_args__ = (
        Index("idx_matches_alert_filing", "alert_id", "filing_id", unique=True),
        Index(
            "idx_matches_pending",
            "notified_at",
            postgresql_where=(notification_status == 'pending')
        ),
        {"comment": "Alert matches and notification tracking"}
    )

    def __repr__(self) -> str:
        """String representation of AlertMatch."""
        return (
            f"<AlertMatch(id={self.id}, alert_id={self.alert_id}, "
            f"filing_id={self.filing_id}, status={self.notification_status})>"
        )
