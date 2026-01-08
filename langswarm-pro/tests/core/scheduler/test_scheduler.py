import pytest
import asyncio
from datetime import datetime, timedelta
from langswarm_pro.core.scheduler.models import Job, JobType, JobStatus
from langswarm_pro.core.scheduler.manager import JobManager
from langswarm_pro.tools.scheduler_tools import RecurringTaskTool, RecurringTaskInput

class TestJobManager:
    @pytest.mark.asyncio
    async def test_schedule_and_retrieve_job(self):
        manager = JobManager()
        job = Job(
            agent_id="agent1",
            task_name="test_task",
            next_run_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        await manager.schedule_job(job)
        retrieved = await manager.get_job(job.id)
        assert retrieved.id == job.id
        assert retrieved.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_get_due_jobs(self):
        manager = JobManager()
        # Due job
        job1 = Job(
            agent_id="a1",
            task_name="due",
            next_run_at=datetime.utcnow() - timedelta(minutes=1)
        )
        # Future job
        job2 = Job(
            agent_id="a1", 
            task_name="future",
            next_run_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        await manager.schedule_job(job1)
        await manager.schedule_job(job2)
        
        due = await manager.get_due_jobs()
        assert len(due) == 1
        assert due[0].id == job1.id

    @pytest.mark.asyncio
    async def test_cancel_job(self):
        manager = JobManager()
        job = Job(agent_id="a1", task_name="t1", next_run_at=datetime.utcnow())
        await manager.schedule_job(job)
        
        success = await manager.cancel_job(job.id)
        assert success
        
        updated = await manager.get_job(job.id)
        assert updated.status == JobStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_mark_running_and_complete(self):
        manager = JobManager()
        job = Job(agent_id="a1", task_name="t1", next_run_at=datetime.utcnow())
        await manager.schedule_job(job)
        
        await manager.mark_running(job.id)
        updated = await manager.get_job(job.id)
        assert updated.status == JobStatus.RUNNING
        
        await manager.mark_completed(job.id)
        final = await manager.get_job(job.id)
        assert final.status == JobStatus.COMPLETED
        assert final.execution_count == 1
        assert final.last_run_at is not None

class TestRecurringTaskTool:
    @pytest.mark.asyncio
    async def test_tool_scheduling(self):
        tool = RecurringTaskTool()
        result = await tool._run(
            task_name="daily_report",
            schedule="0 9 * * *",
            arguments={"target": "manager"}
        )
        
        assert "Successfully scheduled" in result
        
        # Verify it was added to the global manager
        from langswarm_pro.core.scheduler.manager import job_manager
        # We need to find the job we just added. Since jobs have UUIDs, we search by task name.
        # Note: In a real test we might want to dependency inject a fresh manager or mocking.
        # Here we rely on the global instance for the tool test.
        
        found = False
        for job in job_manager._jobs.values():
            if job.task_name == "daily_report":
                found = True
                assert job.job_type == JobType.RECURRING
                assert job.schedule_expression == "0 9 * * *"
                break
        assert found
