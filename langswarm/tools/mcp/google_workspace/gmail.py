import base64
import logging
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from langswarm.tools.core import UnifiedTool
from langswarm.core.errors import ErrorContext
from .auth import GoogleAuth

logger = logging.getLogger(__name__)

class GmailTool(UnifiedTool):
    """
    The 'Secretary' - Gmail integration for reading and sending emails.
    """
    
    metadata = {
        "name": "gmail_tool",
        "description": "Manage Gmail: read threads, create drafts, and send emails.",
        "version": "1.0.0",
        "methods": {
            "list_threads": {
                "description": "List and summarize recent email threads",
                "parameters": {
                    "max_results": {"type": "integer", "description": "Number of threads to retrieve (default: 5)"},
                    "query": {"type": "string", "description": "Search query (e.g., 'from:accountant', 'is:unread')"}
                },
                "required": []
            },
            "create_draft": {
                "description": "Create a draft email reply or new message",
                "parameters": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"},
                    "thread_id": {"type": "string", "description": "Thread ID to reply to (optional)"}
                },
                "required": ["to", "subject", "body"]
            },
            "send_email": {
                "description": "Send an email immediately (Use with caution)",
                "parameters": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    def __init__(self, user_id: str = "default", credentials_path: str = "credentials.json", token_dir: str = "tokens"):
        self.user_id = user_id
        self.auth = GoogleAuth(credentials_path, token_dir)
        self.service = None

    async def initialize(self, config: Dict[str, Any] = None):
        """Initialize Gmail service"""
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

            self.service = build('gmail', 'v1', credentials=creds)
            logger.info(f"Gmail service initialized successfully for user '{self.user_id}'")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            raise

    async def execute(self, input_data: Dict[str, Any], context: ErrorContext = None) -> Dict[str, Any]:
        """Execute Gmail operations"""
        if not self.service:
            await self.initialize()
            
        method = input_data.get("method")
        params = input_data.get("params", {})
        
        try:
            if method == "list_threads":
                return self._list_threads(params.get("max_results", 5), params.get("query", ""))
            elif method == "create_draft":
                return self._create_draft(
                    params["to"], 
                    params["subject"], 
                    params["body"], 
                    params.get("thread_id")
                )
            elif method == "send_email":
                return self._send_email(
                    params["to"], 
                    params["subject"], 
                    params["body"]
                )
            else:
                return {"success": False, "error": f"Unknown method: {method}"}
                
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return {"success": False, "error": str(error)}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": str(e)}

    def _list_threads(self, max_results: int, query: str) -> Dict[str, Any]:
        """List recent threads"""
        results = self.service.users().threads().list(
            userId='me', maxResults=max_results, q=query
        ).execute()
        threads = results.get('threads', [])

        thread_summaries = []
        for thread in threads:
            t_data = self.service.users().threads().get(userId='me', id=thread['id']).execute()
            messages = t_data.get('messages', [])
            if not messages:
                continue
                
            last_msg = messages[-1]
            snippet = last_msg.get('snippet', '')
            headers = last_msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            thread_summaries.append({
                "id": thread['id'],
                "subject": subject,
                "sender": sender,
                "snippet": snippet
            })
            
        return {"success": True, "threads": thread_summaries}

    def _create_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Create a MIME message"""
        message = MIMEText(body)
        message['to'] = to
        message['from'] = "me"
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw}

    def _create_draft(self, to: str, subject: str, body: str, thread_id: str = None) -> Dict[str, Any]:
        """Create a draft email"""
        message = self._create_message(to, subject, body)
        
        if thread_id:
            message['threadId'] = thread_id
            
        draft = self.service.users().drafts().create(
            userId='me', body={'message': message}
        ).execute()
        
        return {"success": True, "draft_id": draft['id'], "message": "Draft created successfully"}

    def _send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email"""
        message = self._create_message(to, subject, body)
        sent_message = self.service.users().messages().send(
            userId='me', body=message
        ).execute()
        
        return {"success": True, "message_id": sent_message['id'], "message": "Email sent successfully"}
