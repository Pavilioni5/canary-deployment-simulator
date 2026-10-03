"""
SQLAlchemy ORM Model for Structured Application & Canary System Logs.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class DeploymentLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False, index=True)
    level = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    source = Column(String(50), default="SIMULATOR", nullable=False)  # ROUTER, SIMULATOR, MONITOR, SYSTEM
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    # Relationships
    deployment = relationship("Deployment", back_populates="logs")

    def __repr__(self):
        return f"<DeploymentLog(id={self.id}, level='{self.level}', source='{self.source}')>"
