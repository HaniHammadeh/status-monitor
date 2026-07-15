from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str = Field(..., max_length=100)
    url: str = Field(..., max_length=500)
    method: str = "GET"
    expected_status: int = 200
    check_interval_seconds: int = 60


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    method: str
    expected_status: int
    check_interval_seconds: int
    is_active: bool
    created_at: datetime


class CheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    checked_at: datetime


class ServiceStatus(BaseModel):
    service: ServiceRead
    current_status: str
    last_checked_at: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    uptime_percent_24h: float
    recent_history: list[str] = []
