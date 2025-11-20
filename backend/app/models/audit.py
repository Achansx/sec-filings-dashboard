"""Audit log model for tracking user actions."""
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    """
    Model for audit logging.

    Tracks all significant user actions for security and compliance purposes.
    """

    __tablename__ = "audit_logs"

    # Primary Key
    id = Column(BigInteger, primary_key=True, index=True, comment="Auto-incrementing ID")

    # User relationship (nullable to support system actions)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to user who performed action"
    )

    # Action Information
    action = Column(String(50), nullable=False, index=True, comment="Action performed")
    resource_type = Column(String(50), nullable=True, comment="Type of resource affected")
    resource_id = Column(String(255), nullable=True, comment="ID of resource affected")
    details = Column(JSONB, nullable=True, comment="Additional action details as JSON")

    # Request Information
    ip_address = Column(INET, nullable=True, comment="IP address of requester")

    # Timestamp
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Action timestamp"
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index("idx_audit_user_created", "user_id", "created_at"),
        Index("idx_audit_action_created", "action", "created_at"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        {"comment": "Audit log for user actions and system events"}
    )

    def __repr__(self) -> str:
        """String representation of AuditLog."""
        return (
            f"<AuditLog(id={self.id}, user_id={self.user_id}, "
            f"action={self.action}, resource={self.resource_type})>"
        )
