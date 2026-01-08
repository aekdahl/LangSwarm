import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from .models import ApprovalRequest, ApprovalStatus

class PersistenceLayer(ABC):
    @abstractmethod
    async def save_request(self, request: ApprovalRequest) -> None:
        pass
        
    @abstractmethod
    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        pass
        
    @abstractmethod
    async def update_request(self, request: ApprovalRequest) -> None:
        pass
        
    @abstractmethod
    async def list_pending_requests(self) -> List[ApprovalRequest]:
        pass

class InMemoryPersistence(PersistenceLayer):
    def __init__(self):
        self._storage: Dict[str, ApprovalRequest] = {}
        
    async def save_request(self, request: ApprovalRequest) -> None:
        self._storage[request.id] = request
        
    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._storage.get(request_id)
        
    async def update_request(self, request: ApprovalRequest) -> None:
        self._storage[request.id] = request
        
    async def list_pending_requests(self) -> List[ApprovalRequest]:
        return [
            req for req in self._storage.values() 
            if req.status == ApprovalStatus.PENDING
        ]

class ApprovalQueue:
    def __init__(self, persistence: PersistenceLayer = None):
        self.persistence = persistence or InMemoryPersistence()
        
    async def create_request(self, agent_id: str, tool_name: str, tool_args: Dict[str, Any], **kwargs) -> ApprovalRequest:
        request = ApprovalRequest(
            agent_id=agent_id,
            tool_name=tool_name,
            tool_args=tool_args,
            **kwargs
        )
        await self.persistence.save_request(request)
        return request
        
    async def approve_request(self, request_id: str, approver_id: str, notes: str = None) -> ApprovalRequest:
        request = await self.persistence.get_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
            
        request.status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approval_notes = notes
        
        await self.persistence.update_request(request)
        return request
        
    async def reject_request(self, request_id: str, rejector_id: str, notes: str = None) -> ApprovalRequest:
        request = await self.persistence.get_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
            
        request.status = ApprovalStatus.REJECTED
        request.approved_by = rejector_id # overloaded field for decision maker
        request.approval_notes = notes
        
        await self.persistence.update_request(request)
        return request

    async def get_pending_requests(self) -> List[ApprovalRequest]:
        return await self.persistence.list_pending_requests()
