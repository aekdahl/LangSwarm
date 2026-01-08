import asyncio
from typing import List, Optional, Dict
from datetime import datetime
from .models import Job, JobStatus, JobType

class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        
    async def schedule_job(self, job: Job) -> Job:
        """Schedule a new job."""
        self._jobs[job.id] = job
        return job
        
    async def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)
        
    async def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.CANCELLED
            return True
        return False
        
    async def get_due_jobs(self) -> List[Job]:
        """Get jobs that are due for execution."""
        now = datetime.utcnow()
        return [
            job for job in self._jobs.values()
            if job.status == JobStatus.PENDING 
            and job.next_run_at <= now
        ]
        
    async def mark_running(self, job_id: str):
        if job := self._jobs.get(job_id):
            job.status = JobStatus.RUNNING

    async def mark_completed(self, job_id: str):
        if job := self._jobs.get(job_id):
            job.status = JobStatus.COMPLETED
            job.last_run_at = datetime.utcnow()
            job.execution_count += 1

job_manager = JobManager()
