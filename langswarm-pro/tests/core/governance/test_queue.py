import pytest
from datetime import datetime, timedelta
from langswarm_pro.core.governance.models import ApprovalStatus, ActionPriority, ApprovalRequest
from langswarm_pro.core.governance.queue import ApprovalQueue, InMemoryPersistence

class TestApprovalQueue:
    @pytest.mark.asyncio
    async def test_create_approval_request(self):
        queue = ApprovalQueue(persistence=InMemoryPersistence())
        
        request = await queue.create_request(
            agent_id="test_agent",
            tool_name="delete_database",
            tool_args={"db_name": "prod"},
            requester_metadata={"reason": "cleanup"}
        )
        
        assert request.id is not None
        assert request.status == ApprovalStatus.PENDING
        assert request.agent_id == "test_agent"
        assert request.tool_name == "delete_database"
        assert request.requester_metadata["reason"] == "cleanup"
        
    @pytest.mark.asyncio
    async def test_approve_request(self):
        queue = ApprovalQueue(persistence=InMemoryPersistence())
        creation = await queue.create_request("agent_1", "deploy", {})
        
        updated = await queue.approve_request(
            request_id=creation.id,
            approver_id="admin_user",
            notes="Looks good"
        )
        
        assert updated.status == ApprovalStatus.APPROVED
        assert updated.approved_by == "admin_user"
        assert updated.approval_notes == "Looks good"
        
    @pytest.mark.asyncio
    async def test_reject_request(self):
        queue = ApprovalQueue(persistence=InMemoryPersistence())
        creation = await queue.create_request("agent_1", "deploy", {})
        
        updated = await queue.reject_request(
            request_id=creation.id,
            rejector_id="admin_user",
            notes="Too risky"
        )
        
        assert updated.status == ApprovalStatus.REJECTED
        assert updated.approved_by == "admin_user"
        assert updated.approval_notes == "Too risky"

    @pytest.mark.asyncio
    async def test_pending_list(self):
        queue = ApprovalQueue(persistence=InMemoryPersistence())
        await queue.create_request("a1", "t1", {})
        await queue.create_request("a2", "t2", {})
        
        # Approve one
        req = (await queue.get_pending_requests())[0]
        await queue.approve_request(req.id, "admin")
        
        pending = await queue.get_pending_requests()
        assert len(pending) == 1
