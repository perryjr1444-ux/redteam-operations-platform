"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class TemplateBase(BaseModel):
    """Base template schema."""

    template_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=50)
    risk_level: str = Field(..., pattern="^(low|medium|high)$")
    duration: str = Field(..., min_length=1, max_length=50)


class TemplateCreate(TemplateBase):
    """Schema for creating a template."""

    pass


class TemplateResponse(TemplateBase):
    """Schema for template response."""

    id: int

    class Config:
        from_attributes = True


class ExerciseBase(BaseModel):
    """Base exercise schema."""

    template: str = Field(..., min_length=1)
    state: str = Field(default="draft", pattern="^(draft|active|completed|archived)$")
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    start_date: Optional[str] = None
    owner: str = Field(..., min_length=1, max_length=100)


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise."""

    scope: Optional[str] = Field(None, max_length=500)


class ExerciseResponse(ExerciseBase):
    """Schema for exercise response."""

    id: int
    exercise_id: str

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str
    environment: str
    database: str
    timestamp: datetime


class MetricsResponse(BaseModel):
    """Metrics response schema."""

    label: str
    value: int = Field(..., ge=0, le=100)


# ============================================================================
# Attack Chain Schemas
# ============================================================================

class ChainStepSchema(BaseModel):
    """Schema for an attack chain step"""
    id: Optional[str] = None  # Auto-generated if not provided
    tool: str
    args: List[Any] = Field(default_factory=list)  # Changed to List to match test format
    depends_on: List[str] = Field(default_factory=list)
    data_mapping: Dict[str, str] = Field(default_factory=dict)
    condition: Optional[str] = None
    parallel: bool = False
    on_error: str = Field(default="stop", pattern="^(stop|continue|skip_remaining)$")
    description: Optional[str] = None


class AttackChainBase(BaseModel):
    """Base attack chain schema"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    risk_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    steps: List[ChainStepSchema]
    metadata: Optional[Dict[str, Any]] = None


class AttackChainCreate(AttackChainBase):
    """Schema for creating an attack chain"""
    chain_id: Optional[str] = None  # Auto-generated if not provided
    is_template: bool = False


class AttackChainUpdate(BaseModel):
    """Schema for updating an attack chain"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    steps: Optional[List[ChainStepSchema]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AttackChainResponse(AttackChainBase):
    """Schema for attack chain response"""
    id: int
    chain_id: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_template: bool
    is_active: bool

    class Config:
        from_attributes = True


class ChainExecutionCreate(BaseModel):
    """Schema for starting a chain execution"""
    chain_id: str
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChainExecutionResponse(BaseModel):
    """Schema for chain execution response"""
    id: int
    execution_id: str
    chain_id: str
    chain_name: Optional[str]
    status: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    results: Optional[List[Dict[str, Any]]] = None
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    executed_by: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
