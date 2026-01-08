from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, UUID4
import uuid

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class ActionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    tool_name: str
    tool_args: Dict[str, Any]
    status: ApprovalStatus = ApprovalStatus.PENDING
    priority: ActionPriority = ActionPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    requester_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit trail
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
