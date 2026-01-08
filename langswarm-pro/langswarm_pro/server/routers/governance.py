from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from ..auth import get_current_user, get_current_admin, User
from ...core.governance.queue import ApprovalQueue, InMemoryPersistence
from ...core.governance.models import ApprovalRequest

# In a real app, this would be a singleton injected dependency
# For now, we instantiate a global queue (persisted in memory)
# Ideally, this should share state with the background worker
_queue = ApprovalQueue(persistence=InMemoryPersistence())

router = APIRouter()

@router.get("/queue", response_model=List[ApprovalRequest])
async def get_pending_requests(
    current_user: User = Depends(get_current_admin)
):
    """
    Get all pending approval requests.
    Requires Admin privileges.
    """
    return await _queue.get_pending_requests()

@router.post("/approve/{request_id}", response_model=ApprovalRequest)
async def approve_request(
    request_id: str,
    notes: str = Body(None, embed=True),
    current_user: User = Depends(get_current_admin)
):
    """
    Approve a request.
    Requires Admin privileges.
    """
    try:
        return await _queue.approve_request(request_id, current_user.id, notes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/reject/{request_id}", response_model=ApprovalRequest)
async def reject_request(
    request_id: str,
    notes: str = Body(None, embed=True),
    current_user: User = Depends(get_current_admin)
):
    """
    Reject a request.
    Requires Admin privileges.
    """
    try:
        return await _queue.reject_request(request_id, current_user.id, notes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
