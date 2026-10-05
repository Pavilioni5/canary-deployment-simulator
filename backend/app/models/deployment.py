"""
SQLAlchemy ORM Models for Deployments, Deployment Versions, and Traffic Configuration.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, ROLLED_BACK
    rollback_threshold = Column(Float, default=10.0, nullable=False)  # Error rate percentage threshold (e.g. 10.0%)
    evaluation_window_seconds = Column(Integer, default=60, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="deployments")
    versions = relationship("DeploymentVersion", back_populates="deployment", cascade="all, delete-orphan")
    traffic_config = relationship("TrafficConfig", back_populates="deployment", uselist=False, cascade="all, delete-orphan")
    metrics = relationship("Metric", back_populates="deployment", cascade="all, delete-orphan")
    events = relationship("DeploymentEvent", back_populates="deployment", cascade="all, delete-orphan")
    logs = relationship("DeploymentLog", back_populates="deployment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Deployment(id={self.id}, name='{self.name}', status='{self.status}')>"


class DeploymentVersion(Base):
    __tablename__ = "deployment_versions"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False)
    version_tag = Column(String(50), nullable=False)  # e.g. "v1.0.0", "v2.0.0"
    version_type = Column(String(20), nullable=False)  # "STABLE" or "CANARY"
    image_tag = Column(String(100), default="latest", nullable=False)
    simulated_latency_ms = Column(Float, default=50.0, nullable=False)
    failure_rate = Column(Float, default=0.0, nullable=False)  # Range 0.0 to 1.0 (e.g. 0.3 = 30% errors)
    error_type = Column(String(50), default="HTTP_500", nullable=True)  # HTTP_500, LATENCY_TIMEOUT, DATABASE_ERROR, MEMORY_SPIKE
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    deployment = relationship("Deployment", back_populates="versions")

    def __repr__(self):
        return f"<DeploymentVersion(id={self.id}, tag='{self.version_tag}', type='{self.version_type}', failure_rate={self.failure_rate})>"


class TrafficConfig(Base):
    __tablename__ = "traffic_configs"

    id = Column(Integer, primary_key=True, index=True)
    deployment_id = Column(Integer, ForeignKey("deployments.id", ondelete="CASCADE"), unique=True, nullable=False)
    stable_percentage = Column(Float, default=100.0, nullable=False)  # 0.0 to 100.0
    canary_percentage = Column(Float, default=0.0, nullable=False)    # 0.0 to 100.0
    last_shifted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    deployment = relationship("Deployment", back_populates="traffic_config")

    def __repr__(self):
        return f"<TrafficConfig(deployment_id={self.deployment_id}, stable={self.stable_percentage}%, canary={self.canary_percentage}%)>"
