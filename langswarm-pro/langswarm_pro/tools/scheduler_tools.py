from datetime import datetime, timedelta
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, Field

from langswarm.tools.base import BaseTool
from langswarm_pro.core.scheduler.manager import job_manager
from langswarm_pro.core.scheduler.models import Job, JobType, JobStatus

class RecurringTaskInput(BaseModel):
    task_name: str = Field(..., description="Name of the task to schedule")
    schedule: str = Field(..., description="Cron expression or ISO interval")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the task")
    start_time: Optional[str] = Field(None, description="ISO timestamp for first run")

class RecurringTaskTool(BaseTool):
    name: str = "schedule_recurring_task"
    description: str = "Schedule a recurring task to be executed by the agent system."
    args_schema: Type[BaseModel] = RecurringTaskInput

    def __init__(self):
        super().__init__(
            tool_id=self.name,
            name=self.name,
            description=self.description,
            version="1.0.0"
        )
    
    async def _run(self, task_name: str, schedule: str, arguments: Dict[str, Any] = None, start_time: str = None) -> str:
        try:
            # Parse start time or default to now + interval (simplified)
            next_run = datetime.utcnow() # In real impl, parse cron/interval
            if start_time:
                next_run = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            
            job = Job(
                agent_id="current_agent", # Context needed in real app
                task_name=task_name,
                arguments=arguments or {},
                job_type=JobType.RECURRING,
                schedule_expression=schedule,
                next_run_at=next_run
            )
            
            await job_manager.schedule_job(job)
            return f"Successfully scheduled recurring task '{task_name}' (ID: {job.id}) to run at {next_run.isoformat()}"
            
        except Exception as e:
            return f"Failed to schedule task: {str(e)}"
