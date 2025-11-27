import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from langswarm.tools.core import UnifiedTool
from langswarm.core.errors import ErrorContext
from .auth import GoogleAuth

logger = logging.getLogger(__name__)

class CalendarTool(UnifiedTool):
    """
    The 'Chief of Staff' - Google Calendar integration for managing schedules.
    """
    
    metadata = {
        "name": "calendar_tool",
        "description": "Manage Google Calendar: list events and create new events.",
        "version": "1.0.0",
        "methods": {
            "list_events": {
                "description": "List upcoming calendar events",
                "parameters": {
                    "max_results": {"type": "integer", "description": "Number of events to retrieve (default: 10)"},
                    "time_min": {"type": "string", "description": "Start time (ISO format), defaults to now"},
                    "time_max": {"type": "string", "description": "End time (ISO format)"}
                },
                "required": []
            },
            "create_event": {
                "description": "Create a new calendar event",
                "parameters": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Start time (ISO format, e.g., '2023-12-25T09:00:00')"},
                    "end_time": {"type": "string", "description": "End time (ISO format)"},
                    "description": {"type": "string", "description": "Event description (optional)"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendee emails (optional)"}
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    }
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, user_id: str = "default", credentials_path: str = "credentials.json", token_dir: str = "tokens"):
        self.user_id = user_id
        self.auth = GoogleAuth(credentials_path, token_dir)
        self.service = None

    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize Calendar service"""
        try:
            # If config provides user_id, update it
            if config and "user_id" in config:
                self.user_id = config["user_id"]
                
            creds = self.auth.get_user_credentials(self.user_id)
            
            # Fallback to interactive auth for "default" user only (backward compatibility)
            if (not creds or not creds.valid) and self.user_id == "default":
                logger.info("No valid credentials found for default user, triggering desktop auth...")
                creds = self.auth.authenticate(self.SCOPES)
            
            if not creds or not creds.valid:
                raise ValueError(f"No valid credentials found for user '{self.user_id}'. Please authenticate via web flow.")

            self.service = build('calendar', 'v3', credentials=creds)
            logger.info(f"Calendar service initialized successfully for user '{self.user_id}'")
        except Exception as e:
            logger.error(f"Failed to initialize Calendar service: {e}")
            raise

    async def execute(self, input_data: Dict[str, Any], context: ErrorContext = None) -> Dict[str, Any]:
        """Execute Calendar operations"""
        if not self.service:
            await self.initialize()
            
        method = input_data.get("method")
        params = input_data.get("params", {})
        
        try:
            if method == "list_events":
                return self._list_events(
                    params.get("max_results", 10),
                    params.get("time_min"),
                    params.get("time_max")
                )
            elif method == "create_event":
                return self._create_event(
                    params["summary"],
                    params["start_time"],
                    params["end_time"],
                    params.get("description"),
                    params.get("attendees", [])
                )
            else:
                return {"success": False, "error": f"Unknown method: {method}"}
                
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return {"success": False, "error": str(error)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def _list_events(self, max_results: int, time_min: str = None, time_max: str = None) -> Dict[str, Any]:
        """List upcoming events"""
        if not time_min:
            time_min = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
        events_result = self.service.events().list(
            calendarId='primary', timeMin=time_min, timeMax=time_max,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        event_summaries = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_summaries.append({
                "id": event['id'],
                "summary": event['summary'],
                "start": start,
                "status": event.get('status')
            })
            
        return {"success": True, "events": event_summaries}

    def _create_event(self, summary: str, start_time: str, end_time: str, description: str = None, attendees: List[str] = []) -> Dict[str, Any]:
        """Create a new event"""
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC', # Assuming UTC for simplicity, could be configurable
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
            'attendees': [{'email': email} for email in attendees],
        }

        created_event = self.service.events().insert(calendarId='primary', body=event).execute()
        
        return {
            "success": True, 
            "event_id": created_event['id'], 
            "link": created_event.get('htmlLink'),
            "message": "Event created successfully"
        }
