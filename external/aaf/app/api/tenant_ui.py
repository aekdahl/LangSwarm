"""
Tenant UI Configuration API
Provides runtime configuration for the AAF widget and SPA
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import jwt
from cachetools import TTLCache
import hashlib

from ..core.config import get_settings
from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["tenant-ui"])

# In-memory cache for UI configs (15 minute TTL)
ui_config_cache = TTLCache(maxsize=1000, ttl=900)


class BrandConfig(BaseModel):
    """Brand configuration for UI theming"""
    primary: str = Field(..., pattern=r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", description="Primary color (hex)")
    accent: Optional[str] = Field(None, description="Accent color")
    font: str = Field(default="Inter", description="Font family")
    logoUrl: Optional[str] = Field(None, description="Logo URL")
    cornerRadius: Optional[float] = Field(default=8, description="Border radius in pixels")


class FeaturesConfig(BaseModel):
    """Feature toggles for the UI"""
    attachments: bool = Field(default=False, description="Enable file attachments")
    allowedFileTypes: list[str] = Field(default=["pdf", "png", "jpg", "txt"], description="Allowed file types")
    downloadTranscripts: bool = Field(default=False, description="Enable transcript downloads")
    suggestedPrompts: list[str] = Field(default=[], description="Suggested prompt buttons")
    showTyping: bool = Field(default=True, description="Show typing indicators")
    i18n: str = Field(default="en", pattern=r"^(en|sv|de|fr)$", description="Language code")


class CopyConfig(BaseModel):
    """UI copy/text configuration"""
    title: str = Field(default="How can we help?", description="Chat widget title")
    subtitle: Optional[str] = Field(None, description="Chat widget subtitle")
    inputPlaceholder: str = Field(default="Type a message...", description="Input placeholder text")
    emptyState: str = Field(default="Start a conversation", description="Empty state message")


class EndpointsConfig(BaseModel):
    """API endpoint configuration"""
    apiBase: str = Field(..., description="Base API URL")
    wsBase: str = Field(..., description="WebSocket base URL")


class ComplianceConfig(BaseModel):
    """Compliance and legal configuration"""
    piiConsentBanner: bool = Field(default=False, description="Show PII consent banner")
    telemetryOptIn: bool = Field(default=False, description="Show telemetry opt-in")
    termsUrl: Optional[str] = Field(None, description="Terms of service URL")
    privacyUrl: Optional[str] = Field(None, description="Privacy policy URL")


class FlagsConfig(BaseModel):
    """Feature flags and limits"""
    betaFeatures: list[str] = Field(default=[], description="Enabled beta features")
    maxToolCalls: int = Field(default=3, description="Maximum tool calls per conversation")


class UIConfig(BaseModel):
    """Complete UI configuration response"""
    brand: BrandConfig
    features: FeaturesConfig
    copy: CopyConfig
    endpoints: EndpointsConfig
    compliance: Optional[ComplianceConfig] = None
    flags: Optional[FlagsConfig] = None


class SessionRequest(BaseModel):
    """Session creation request"""
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional session metadata")


class SessionResponse(BaseModel):
    """Session creation response"""
    session_id: str = Field(..., description="Session identifier")
    jwt: str = Field(..., description="JWT token for authentication")
    expires_at: str = Field(..., description="Token expiration time (ISO format)")


def generate_etag(data: Dict[str, Any]) -> str:
    """Generate ETag for caching"""
    content = json.dumps(data, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


def get_tenant_config(tenant_id: str) -> Dict[str, Any]:
    """Get tenant configuration from database/config"""
    # This would typically fetch from a database
    # For now, return a default configuration with tenant-specific customizations
    
    default_config = {
        "brand": {
            "primary": "#1C55FF",
            "accent": "#64748b",
            "font": "Inter",
            "logoUrl": None,
            "cornerRadius": 12
        },
        "features": {
            "attachments": True,
            "allowedFileTypes": ["pdf", "png", "jpg", "txt", "docx"],
            "downloadTranscripts": False,
            "suggestedPrompts": [
                "How can I get started?",
                "What services do you offer?",
                "I need help with billing"
            ],
            "showTyping": True,
            "i18n": "en"
        },
        "copy": {
            "title": "How can we help?",
            "subtitle": None,
            "inputPlaceholder": "Type your message...",
            "emptyState": "Start a conversation with our AI assistant"
        },
        "endpoints": {
            "apiBase": f"https://{get_settings().app_host}:{get_settings().app_port}",
            "wsBase": f"wss://{get_settings().app_host}:{get_settings().app_port}"
        },
        "compliance": {
            "piiConsentBanner": True,
            "telemetryOptIn": False,
            "termsUrl": None,
            "privacyUrl": None
        },
        "flags": {
            "betaFeatures": [],
            "maxToolCalls": 3
        }
    }
    
    # Apply tenant-specific overrides
    tenant_overrides = {
        "demo": {
            "brand": {"primary": "#2563eb", "accent": "#3b82f6"},
            "copy": {"title": "Demo Chat Assistant"},
            "features": {"suggestedPrompts": ["Try the demo", "What can you do?", "Show me features"]}
        },
        "enterprise": {
            "brand": {"primary": "#059669", "font": "system-ui"},
            "copy": {"title": "Enterprise Support"},
            "features": {"attachments": True, "downloadTranscripts": True},
            "compliance": {"piiConsentBanner": True, "telemetryOptIn": True}
        }
    }
    
    if tenant_id in tenant_overrides:
        override = tenant_overrides[tenant_id]
        for key, value in override.items():
            if isinstance(value, dict):
                default_config[key].update(value)
            else:
                default_config[key] = value
    
    return default_config


@router.get("/{tenant_id}/ui-config", response_model=UIConfig)
async def get_ui_config(
    tenant_id: str,
    request: Request,
    if_none_match: Optional[str] = Header(None)
):
    """
    Get UI configuration for a tenant
    
    Supports ETag caching to reduce bandwidth and improve performance.
    Cache TTL is 15 minutes by default.
    """
    try:
        # Check cache first
        cache_key = f"ui_config:{tenant_id}"
        cached_data = ui_config_cache.get(cache_key)
        
        if cached_data:
            config_data, etag = cached_data
        else:
            # Fetch fresh config
            config_data = get_tenant_config(tenant_id)
            etag = generate_etag(config_data)
            
            # Cache the result
            ui_config_cache[cache_key] = (config_data, etag)
        
        # Check ETag for conditional requests
        if if_none_match and if_none_match.strip('"') == etag:
            return JSONResponse(
                status_code=304,
                headers={"ETag": f'"{etag}"'}
            )
        
        # Validate and return config
        ui_config = UIConfig(**config_data)
        
        return JSONResponse(
            content=ui_config.dict(),
            headers={
                "ETag": f'"{etag}"',
                "Cache-Control": "public, max-age=900",  # 15 minutes
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "If-None-Match"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get UI config for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get UI configuration: {str(e)}"
        )


@router.post("/session", response_model=SessionResponse)
async def create_session(
    session_req: SessionRequest,
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Create a new chat session with JWT authentication
    
    Returns a short-lived JWT (10 minutes) that must be used for chat operations.
    The JWT includes session metadata and can be renewed.
    """
    try:
        settings = get_settings()
        
        # Generate session ID
        import uuid
        session_id = f"sess_{session_req.tenant_id}_{uuid.uuid4().hex[:8]}"
        
        # Create session in LangSwarm manager if available
        if hasattr(manager, 'create_session'):
            await manager.create_session(
                session_id=session_id,
                agent_id=None  # Will use default agent
            )
        
        # Generate JWT
        exp = datetime.utcnow() + timedelta(minutes=10)  # Short-lived token
        
        jwt_payload = {
            "sid": session_id,
            "tid": session_req.tenant_id,
            "uid": session_req.user_id,
            "exp": exp,
            "iat": datetime.utcnow(),
            "iss": "aaf-backend",
            "aud": "aaf-widget"
        }
        
        if session_req.metadata:
            jwt_payload["metadata"] = session_req.metadata
        
        token = jwt.encode(
            jwt_payload,
            settings.secret_key,
            algorithm="HS256"
        )
        
        logger.info(f"Created session {session_id} for tenant {session_req.tenant_id}")
        
        return SessionResponse(
            session_id=session_id,
            jwt=token,
            expires_at=exp.isoformat() + "Z"
        )
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.post("/session/refresh")
async def refresh_session(
    authorization: str = Header(..., description="Bearer token"),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Refresh an existing session JWT
    
    Extends the session lifetime by issuing a new JWT.
    The old JWT should still be valid for a grace period.
    """
    try:
        settings = get_settings()
        
        # Extract token from Authorization header
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        token = authorization[7:]  # Remove "Bearer " prefix
        
        # Decode and validate current JWT
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=["HS256"],
                audience="aaf-widget",
                issuer="aaf-backend"
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        
        # Issue new JWT with same session info
        exp = datetime.utcnow() + timedelta(minutes=10)
        
        new_payload = {
            "sid": payload["sid"],
            "tid": payload["tid"],
            "uid": payload.get("uid"),
            "exp": exp,
            "iat": datetime.utcnow(),
            "iss": "aaf-backend",
            "aud": "aaf-widget"
        }
        
        if "metadata" in payload:
            new_payload["metadata"] = payload["metadata"]
        
        new_token = jwt.encode(
            new_payload,
            settings.secret_key,
            algorithm="HS256"
        )
        
        return SessionResponse(
            session_id=payload["sid"],
            jwt=new_token,
            expires_at=exp.isoformat() + "Z"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh session: {str(e)}"
        )


@router.get("/{tenant_id}/config/schema")
async def get_ui_config_schema(tenant_id: str):
    """
    Get JSON schema for UI configuration
    
    Useful for validation and form generation in admin interfaces.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "AAF UI Config",
        "type": "object",
        "required": ["brand", "features", "copy", "endpoints"],
        "properties": {
            "brand": {
                "type": "object",
                "properties": {
                    "primary": {"type": "string", "pattern": "^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"},
                    "accent": {"type": "string"},
                    "font": {"type": "string"},
                    "logoUrl": {"type": "string", "format": "uri"},
                    "cornerRadius": {"type": "number"}
                }
            },
            "features": {
                "type": "object",
                "properties": {
                    "attachments": {"type": "boolean"},
                    "allowedFileTypes": {"type": "array", "items": {"type": "string"}},
                    "downloadTranscripts": {"type": "boolean"},
                    "suggestedPrompts": {"type": "array", "items": {"type": "string"}},
                    "showTyping": {"type": "boolean"},
                    "i18n": {"type": "string", "enum": ["en", "sv", "de", "fr"]}
                }
            },
            "copy": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "subtitle": {"type": "string"},
                    "inputPlaceholder": {"type": "string"},
                    "emptyState": {"type": "string"}
                }
            },
            "endpoints": {
                "type": "object",
                "required": ["apiBase", "wsBase"],
                "properties": {
                    "apiBase": {"type": "string", "format": "uri"},
                    "wsBase": {"type": "string", "format": "uri"}
                }
            },
            "compliance": {
                "type": "object",
                "properties": {
                    "piiConsentBanner": {"type": "boolean"},
                    "telemetryOptIn": {"type": "boolean"},
                    "termsUrl": {"type": "string", "format": "uri"},
                    "privacyUrl": {"type": "string", "format": "uri"}
                }
            },
            "flags": {
                "type": "object",
                "properties": {
                    "betaFeatures": {"type": "array", "items": {"type": "string"}},
                    "maxToolCalls": {"type": "number"}
                }
            }
        }
    }


def verify_jwt_token(authorization: str) -> Dict[str, Any]:
    """
    Verify JWT token and return payload
    
    Used by other endpoints that require authentication.
    """
    settings = get_settings()
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization[7:]
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=["HS256"],
            audience="aaf-widget",
            issuer="aaf-backend"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# Dependency for JWT authentication
async def get_current_session(authorization: str = Header(...)) -> Dict[str, Any]:
    """FastAPI dependency for JWT authentication"""
    return verify_jwt_token(authorization)
