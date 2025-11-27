import os
import pickle
import logging
from typing import Optional, List, Tuple

from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

logger = logging.getLogger(__name__)

class GoogleAuth:
    """Handles Google OAuth 2.0 authentication for multiple users"""
    
    def __init__(self, credentials_path: str = "credentials.json", token_dir: str = "tokens"):
        self.credentials_path = credentials_path
        self.token_dir = token_dir
        
        if not os.path.exists(token_dir):
            os.makedirs(token_dir)

    def get_user_credentials(self, user_id: str) -> Optional[Credentials]:
        """Retrieve credentials for a specific user"""
        token_path = os.path.join(self.token_dir, f"{user_id}.pickle")
        creds = None
        
        if os.path.exists(token_path):
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Failed to load token for user {user_id}: {e}")
        
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info(f"Refreshing expired token for user {user_id}...")
                creds.refresh(Request())
                self.save_user_credentials(user_id, creds)
            except Exception as e:
                logger.warning(f"Failed to refresh token for user {user_id}: {e}")
                return None
                
        return creds

    def save_user_credentials(self, user_id: str, creds: Credentials):
        """Save credentials for a specific user"""
        token_path = os.path.join(self.token_dir, f"{user_id}.pickle")
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
            
    def authenticate(self, scopes: List[str]) -> Credentials:
        """Authenticate default user (desktop flow) - Backward compatibility"""
        user_id = "default"
        creds = self.get_user_credentials(user_id)
        
        if not creds or not creds.valid:
            if not os.path.exists(self.credentials_path):
                raise FileNotFoundError(
                    f"Credentials file not found at {self.credentials_path}. "
                    "Please download it from Google Cloud Console."
                )
            
            logger.info("Starting OAuth flow (Desktop)...")
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, scopes
            )
            creds = flow.run_local_server(port=0)
            self.save_user_credentials(user_id, creds)
        
        return creds

class WebAuthHelper:
    """Helper for Web-based OAuth flow integration"""
    
    def __init__(self, credentials_path: str = "credentials.json", scopes: List[str] = None, redirect_uri: str = "http://localhost:8000/oauth2callback"):
        self.credentials_path = credentials_path
        self.scopes = scopes or [
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/calendar'
        ]
        self.redirect_uri = redirect_uri

    def get_authorization_url(self) -> Tuple[str, str]:
        """Generate authorization URL and state"""
        if not os.path.exists(self.credentials_path):
             raise FileNotFoundError(f"Credentials file not found at {self.credentials_path}")

        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return authorization_url, state

    def fetch_token(self, code: str) -> Credentials:
        """Exchange authorization code for credentials"""
        flow = Flow.from_client_secrets_file(
            self.credentials_path,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        flow.fetch_token(code=code)
        return flow.credentials
