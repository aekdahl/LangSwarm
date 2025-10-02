"""
LangSwarm V2 Live Collaboration Manager

Live collaboration and multi-user session support for V2 agents with
real-time synchronization, participant management, and shared context.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
import uuid

from .interfaces import (
    ILiveCollaboration, CollaborationState, RealtimeMessage, RealtimeEvent,
    RealtimeConfiguration, CollaborationRole, EventType, RealtimeError
)


class LiveCollaborationSession(ILiveCollaboration):
    """
    Live collaboration session for multi-user agent interactions.
    
    Provides real-time collaboration capabilities including participant
    management, message broadcasting, and shared context synchronization.
    """
    
    def __init__(self, config: RealtimeConfiguration):
        """
        Initialize live collaboration session.
        
        Args:
            config: Real-time configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Session state
        self._session_id: Optional[str] = None
        self._state = CollaborationState()
        self._active = False
        self._created_at: Optional[datetime] = None
        
        # Participant management
        self._participants: Dict[str, CollaborationRole] = {}
        self._participant_connections: Dict[str, Any] = {}  # Connection handles
        self._active_speaker: Optional[str] = None
        
        # Message handling
        self._message_history: List[RealtimeMessage] = []
        self._message_queue = asyncio.Queue()
        self._event_queue = asyncio.Queue()
        
        # Shared context
        self._shared_context: Dict[str, Any] = {}
        self._context_lock = asyncio.Lock()
        
        # Background tasks
        self._message_processing_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "session_start_time": None,
            "total_participants": 0,
            "messages_exchanged": 0,
            "context_updates": 0,
            "active_duration": 0.0
        }
        
        self._logger.debug("Live collaboration session initialized")
    
    @property
    def session_id(self) -> str:
        """Collaboration session ID"""
        return self._session_id or ""
    
    @property
    def state(self) -> CollaborationState:
        """Current collaboration state"""
        return self._state
    
    @property
    def participant_count(self) -> int:
        """Number of active participants"""
        return len(self._participants)
    
    @property
    def is_active(self) -> bool:
        """Check if collaboration session is active"""
        return self._active
    
    async def create_session(self, creator_id: str) -> str:
        """
        Create new collaboration session.
        
        Args:
            creator_id: User ID of session creator
            
        Returns:
            Session ID of created session
        """
        try:
            if self._active:
                raise RealtimeError("Session already active")
            
            self._session_id = str(uuid.uuid4())
            self._created_at = datetime.utcnow()
            self._active = True
            
            # Initialize state
            self._state = CollaborationState(
                session_id=self._session_id,
                created_at=self._created_at,
                updated_at=self._created_at
            )
            
            # Add creator as admin
            await self._add_participant_internal(creator_id, CollaborationRole.ADMIN)
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Update statistics
            self._stats["session_start_time"] = self._created_at
            self._stats["total_participants"] = 1
            
            self._logger.info(f"Created collaboration session: {self._session_id}")
            
            # Broadcast session creation event
            await self._broadcast_event(EventType.PARTICIPANT_JOIN, {
                "session_id": self._session_id,
                "participant_id": creator_id,
                "role": CollaborationRole.ADMIN.value,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return self._session_id
            
        except Exception as e:
            self._logger.error(f"Failed to create collaboration session: {e}")
            raise RealtimeError(f"Session creation failed: {e}")
    
    async def join_session(self, session_id: str, participant_id: str, role: CollaborationRole = CollaborationRole.PARTICIPANT) -> bool:
        """
        Join collaboration session.
        
        Args:
            session_id: Session to join
            participant_id: Participant identifier
            role: Participant role
            
        Returns:
            True if join successful
        """
        try:
            if not self._active or self._session_id != session_id:
                raise RealtimeError(f"Session {session_id} not active")
            
            if len(self._participants) >= self.config.max_participants:
                raise RealtimeError("Session at maximum capacity")
            
            if participant_id in self._participants:
                self._logger.warning(f"Participant {participant_id} already in session")
                return True
            
            # Add participant
            await self._add_participant_internal(participant_id, role)
            
            # Update statistics
            self._stats["total_participants"] = max(self._stats["total_participants"], len(self._participants))
            
            self._logger.info(f"Participant {participant_id} joined session {session_id}")
            
            # Broadcast join event
            await self._broadcast_event(EventType.PARTICIPANT_JOIN, {
                "session_id": session_id,
                "participant_id": participant_id,
                "role": role.value,
                "timestamp": datetime.utcnow().isoformat(),
                "participant_count": len(self._participants)
            })
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to join session {session_id}: {e}")
            return False
    
    async def leave_session(self, participant_id: str) -> bool:
        """
        Leave collaboration session.
        
        Args:
            participant_id: Participant to remove
            
        Returns:
            True if leave successful
        """
        try:
            if not self._active:
                return False
            
            if participant_id not in self._participants:
                self._logger.warning(f"Participant {participant_id} not in session")
                return True
            
            # Remove participant
            role = self._participants[participant_id]
            await self._remove_participant_internal(participant_id)
            
            self._logger.info(f"Participant {participant_id} left session {self._session_id}")
            
            # Broadcast leave event
            await self._broadcast_event(EventType.PARTICIPANT_LEAVE, {
                "session_id": self._session_id,
                "participant_id": participant_id,
                "role": role.value,
                "timestamp": datetime.utcnow().isoformat(),
                "participant_count": len(self._participants)
            })
            
            # Close session if no participants left
            if len(self._participants) == 0:
                await self._close_session()
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to leave session: {e}")
            return False
    
    async def broadcast_message(self, message: RealtimeMessage, sender_id: str) -> bool:
        """
        Broadcast message to all participants.
        
        Args:
            message: Message to broadcast
            sender_id: Message sender ID
            
        Returns:
            True if broadcast successful
        """
        try:
            if not self._active:
                self._logger.warning("Cannot broadcast - session not active")
                return False
            
            if sender_id not in self._participants:
                self._logger.warning(f"Sender {sender_id} not in session")
                return False
            
            # Set message metadata
            message.sender_id = sender_id
            message.session_id = self._session_id
            message.timestamp = datetime.utcnow()
            
            # Add to message history
            self._message_history.append(message)
            
            # Queue for broadcasting
            await self._message_queue.put(message)
            
            # Update statistics
            self._stats["messages_exchanged"] += 1
            
            self._logger.debug(f"Queued message for broadcast: {message.id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to broadcast message: {e}")
            return False
    
    async def update_shared_context(self, updates: Dict[str, Any]) -> bool:
        """
        Update shared collaboration context.
        
        Args:
            updates: Context updates to apply
            
        Returns:
            True if update successful
        """
        try:
            if not self._active:
                self._logger.warning("Cannot update context - session not active")
                return False
            
            async with self._context_lock:
                # Apply updates
                self._shared_context.update(updates)
                
                # Update state
                self._state.shared_context = self._shared_context.copy()
                self._state.updated_at = datetime.utcnow()
                
                # Update statistics
                self._stats["context_updates"] += 1
                
                self._logger.debug(f"Updated shared context: {len(updates)} changes")
                
                # Broadcast context update event
                await self._broadcast_event(EventType.MESSAGE_START, {  # Using MESSAGE_START as generic update
                    "type": "context_update",
                    "session_id": self._session_id,
                    "updates": updates,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                return True
            
        except Exception as e:
            self._logger.error(f"Failed to update shared context: {e}")
            return False
    
    async def get_message_history(self, limit: Optional[int] = None) -> List[RealtimeMessage]:
        """
        Get message history for session.
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of messages
        """
        if limit:
            return self._message_history[-limit:]
        return self._message_history.copy()
    
    async def get_participants(self) -> Dict[str, CollaborationRole]:
        """
        Get current session participants.
        
        Returns:
            Dictionary of participant IDs and roles
        """
        return self._participants.copy()
    
    async def set_active_speaker(self, participant_id: str) -> bool:
        """
        Set active speaker for session.
        
        Args:
            participant_id: Participant to set as active speaker
            
        Returns:
            True if set successfully
        """
        try:
            if participant_id not in self._participants:
                return False
            
            self._active_speaker = participant_id
            self._state.active_speaker = participant_id
            self._state.updated_at = datetime.utcnow()
            
            # Broadcast speaker change event
            await self._broadcast_event(EventType.MESSAGE_START, {  # Using MESSAGE_START as generic update
                "type": "speaker_change",
                "session_id": self._session_id,
                "active_speaker": participant_id,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to set active speaker: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get collaboration session statistics.
        
        Returns:
            Dictionary of statistics
        """
        current_time = datetime.utcnow()
        
        if self._created_at:
            self._stats["active_duration"] = (current_time - self._created_at).total_seconds()
        
        return {
            **self._stats,
            "session_id": self._session_id,
            "is_active": self._active,
            "current_participants": len(self._participants),
            "active_speaker": self._active_speaker,
            "message_history_size": len(self._message_history),
            "shared_context_size": len(self._shared_context),
            "queue_sizes": {
                "message_queue": self._message_queue.qsize(),
                "event_queue": self._event_queue.qsize()
            }
        }
    
    async def _add_participant_internal(self, participant_id: str, role: CollaborationRole) -> None:
        """Internal method to add participant"""
        self._participants[participant_id] = role
        self._state.participants[participant_id] = role
        self._state.updated_at = datetime.utcnow()
    
    async def _remove_participant_internal(self, participant_id: str) -> None:
        """Internal method to remove participant"""
        if participant_id in self._participants:
            del self._participants[participant_id]
            del self._state.participants[participant_id]
            
            # Clear active speaker if it was this participant
            if self._active_speaker == participant_id:
                self._active_speaker = None
                self._state.active_speaker = None
            
            self._state.updated_at = datetime.utcnow()
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks"""
        # Start message processing task
        self._message_processing_task = asyncio.create_task(self._message_processing_loop())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks"""
        tasks = [self._message_processing_task, self._cleanup_task]
        
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._message_processing_task = None
        self._cleanup_task = None
    
    async def _message_processing_loop(self) -> None:
        """Background task for processing and broadcasting messages"""
        while self._active:
            try:
                # Get message from queue
                message = await asyncio.wait_for(
                    self._message_queue.get(),
                    timeout=1.0
                )
                
                # Broadcast to all participants except sender
                await self._broadcast_message_to_participants(message)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in message processing loop: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for session cleanup and maintenance"""
        while self._active:
            try:
                # Check for session timeout
                if self._created_at:
                    session_age = (datetime.utcnow() - self._created_at).total_seconds()
                    if session_age > self.config.session_timeout:
                        self._logger.warning(f"Session {self._session_id} timed out")
                        await self._close_session()
                        break
                
                # Cleanup old messages
                if len(self._message_history) > 1000:  # Keep last 1000 messages
                    self._message_history = self._message_history[-1000:]
                
                # Sleep for cleanup interval
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Error in cleanup loop: {e}")
    
    async def _broadcast_message_to_participants(self, message: RealtimeMessage) -> None:
        """Broadcast message to all participants"""
        try:
            # In real implementation, would send to participant connections
            self._logger.debug(f"Broadcasting message {message.id} to {len(self._participants)} participants")
            
            # Simulate broadcasting
            for participant_id in self._participants:
                if participant_id != message.sender_id:
                    # Would send message to participant's connection
                    pass
            
        except Exception as e:
            self._logger.error(f"Failed to broadcast message: {e}")
    
    async def _broadcast_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Broadcast event to all participants"""
        try:
            event = RealtimeEvent(
                type=event_type,
                data=data,
                session_id=self._session_id
            )
            
            # In real implementation, would send to participant connections
            self._logger.debug(f"Broadcasting event {event_type.value} to {len(self._participants)} participants")
            
        except Exception as e:
            self._logger.error(f"Failed to broadcast event: {e}")
    
    async def _close_session(self) -> None:
        """Close collaboration session"""
        try:
            self._logger.info(f"Closing collaboration session: {self._session_id}")
            
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Notify remaining participants
            await self._broadcast_event(EventType.CONNECTION_CLOSE, {
                "session_id": self._session_id,
                "reason": "session_closed",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Clear state
            self._active = False
            self._participants.clear()
            self._message_history.clear()
            self._shared_context.clear()
            
            self._logger.info(f"Collaboration session closed: {self._session_id}")
            
        except Exception as e:
            self._logger.error(f"Error closing session: {e}")


class CollaborationManager:
    """
    Manager for multiple collaboration sessions.
    
    Handles creation, management, and coordination of multiple
    live collaboration sessions.
    """
    
    def __init__(self, config: RealtimeConfiguration):
        """
        Initialize collaboration manager.
        
        Args:
            config: Real-time configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Session management
        self._sessions: Dict[str, LiveCollaborationSession] = {}
        self._participant_sessions: Dict[str, Set[str]] = {}  # participant_id -> session_ids
        
        # Statistics
        self._stats = {
            "total_sessions_created": 0,
            "active_sessions": 0,
            "total_participants": 0,
            "messages_processed": 0
        }
    
    async def create_session(self, creator_id: str) -> Optional[LiveCollaborationSession]:
        """Create new collaboration session"""
        try:
            session = LiveCollaborationSession(self.config)
            session_id = await session.create_session(creator_id)
            
            self._sessions[session_id] = session
            
            # Track participant
            if creator_id not in self._participant_sessions:
                self._participant_sessions[creator_id] = set()
            self._participant_sessions[creator_id].add(session_id)
            
            # Update statistics
            self._stats["total_sessions_created"] += 1
            self._stats["active_sessions"] = len(self._sessions)
            
            self._logger.info(f"Created collaboration session: {session_id}")
            return session
            
        except Exception as e:
            self._logger.error(f"Failed to create collaboration session: {e}")
            return None
    
    async def get_session(self, session_id: str) -> Optional[LiveCollaborationSession]:
        """Get collaboration session by ID"""
        return self._sessions.get(session_id)
    
    async def remove_session(self, session_id: str) -> bool:
        """Remove collaboration session"""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            
            # Remove from participant tracking
            for participant_id, session_ids in self._participant_sessions.items():
                session_ids.discard(session_id)
            
            del self._sessions[session_id]
            self._stats["active_sessions"] = len(self._sessions)
            
            self._logger.info(f"Removed collaboration session: {session_id}")
            return True
        
        return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get collaboration manager statistics"""
        return {
            **self._stats,
            "session_details": {
                session_id: await session.get_statistics()
                for session_id, session in self._sessions.items()
            }
        }


class ParticipantManager:
    """
    Manager for collaboration participants.
    
    Handles participant state, permissions, and cross-session management.
    """
    
    def __init__(self):
        """Initialize participant manager"""
        self._logger = logging.getLogger(__name__)
        
        # Participant tracking
        self._participants: Dict[str, Dict[str, Any]] = {}
        self._participant_sessions: Dict[str, Set[str]] = {}
    
    async def add_participant(self, participant_id: str, metadata: Dict[str, Any]) -> bool:
        """Add participant with metadata"""
        try:
            self._participants[participant_id] = {
                "metadata": metadata,
                "created_at": datetime.utcnow(),
                "last_active": datetime.utcnow(),
                "session_count": 0
            }
            
            self._participant_sessions[participant_id] = set()
            
            self._logger.info(f"Added participant: {participant_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to add participant {participant_id}: {e}")
            return False
    
    async def remove_participant(self, participant_id: str) -> bool:
        """Remove participant"""
        try:
            if participant_id in self._participants:
                del self._participants[participant_id]
                del self._participant_sessions[participant_id]
                
                self._logger.info(f"Removed participant: {participant_id}")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Failed to remove participant {participant_id}: {e}")
            return False


# Factory functions
def create_collaboration_session(config: RealtimeConfiguration) -> LiveCollaborationSession:
    """Create a new collaboration session"""
    return LiveCollaborationSession(config)


async def join_collaboration(session_id: str, participant_id: str, session: LiveCollaborationSession) -> bool:
    """Join an existing collaboration session"""
    return await session.join_session(session_id, participant_id)
