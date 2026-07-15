import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class CheckStatus(str, enum.Enum):
    up = "up"
    down = "down"


class IncidentStatus(str, enum.Enum):
    ongoing = "ongoing"
    resolved = "resolved"


class Service(Base):
    """A single endpoint being monitored, e.g. an API or a website."""

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False, default="GET")
    expected_status = Column(Integer, nullable=False, default=200)
    check_interval_seconds = Column(Integer, nullable=False, default=60)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    checks = relationship(
        "Check", back_populates="service", cascade="all, delete-orphan"
    )
    incidents = relationship(
        "Incident", back_populates="service", cascade="all, delete-orphan"
    )


class Check(Base):
    """A single point-in-time health check result. This is the time-series table."""

    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(Enum(CheckStatus), nullable=False)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    service = relationship("Service", back_populates="checks")


class Incident(Base):
    """
    A continuous span of downtime for a service. Opened when a check first
    fails, resolved when a subsequent check succeeds. Keeps the checks table
    from being the only way to answer 'how many outages has this had'.
    """

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(
        Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.ongoing)

    service = relationship("Service", back_populates="incidents")
