from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, UUID4
import uuid

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    ONE_OFF = "one_off"
    RECURRING = "recurring"
    OPTIMIZATION = "optimization"
    INGESTION = "ingestion"

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    task_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    
    # Scheduling info
    job_type: JobType = JobType.ONE_OFF
    schedule_expression: Optional[str] = None # Cron expression or ISO interval
    next_run_at: datetime
    
    # Execution state
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run_at: Optional[datetime] = None
    execution_count: int = 0
    max_retries: int = 3
    retry_count: int = 0
    failure_reason: Optional[str] = None
