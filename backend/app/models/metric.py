"""
SQLAlchemy ORM Model for Canary & Stable Real-time Metrics.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    version_type = Column(String(20), nullable=False)  # "STABLE", "CANARY", "TOTAL"
    total_requests = Column(Integer, default=0, nullable=False)
    successful_requests = Column(Integer, default=0, nullable=False)
    failed_requests = Column(Integer, default=0, nullable=False)
    error_rate = Column(Float, default=0.0, nullable=False)  # Stored as percentage, e.g. 12.5%
    avg_response_time_ms = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    deployment = relationship("Deployment", back_populates="metrics")

    def __repr__(self):
        return f"<Metric(id={self.id}, deployment_id={self.deployment_id}, version={self.version_type}, errors={self.error_rate}%)>"
