from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import uuid4

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Short title for the task")
    description: Optional[str] = Field(None, max_length=2000, description="Optional detailed description")

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str = Field(default_factory=lambda: str(uuid4()), description="UUIDv4 string identifier")
    is_completed: bool = Field(default=False)
    created_at: str = Field(..., description="UTC ISO8601 timestamp")
    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    is_completed: bool