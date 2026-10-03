"""
SQLAlchemy ORM Model for Deployment Lifecycle & Rollback Audit Events.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class DeploymentEvent(Base):
    __tablename__ = "deployment_events"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # CREATED, TRAFFIC_SHIFT, FAILURE_INJECTED, AUTO_ROLLBACK, MANUAL_ROLLBACK
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON-encoded payload or context
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    deployment = relationship("Deployment", back_populates="events")

    def __repr__(self):
        return f"<DeploymentEvent(id={self.id}, deployment_id={self.deployment_id}, event='{self.event_type}')>"
