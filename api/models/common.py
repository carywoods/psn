"""
Common Pydantic models shared across API endpoints
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid


class Meta(BaseModel):
    """Metadata included in all API responses"""
    api_version: str = Field(..., description="API version")
    model_version: str = Field(..., description="Yeast-GEM model version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")


class ErrorDetail(BaseModel):
    """Structured error information"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response wrapper"""
    error: ErrorDetail
    meta: Meta


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="API status")
    model_loaded: bool = Field(..., description="Whether the COBRA model is loaded")
    database_connected: bool = Field(..., description="Whether the database is accessible")
    uptime_seconds: float = Field(..., description="API uptime in seconds")
    meta: Meta
