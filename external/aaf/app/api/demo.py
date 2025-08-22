"""
Demo API endpoints for AAF Backend
Website reproduction with integrated chat UI for testing and showcasing
"""
import logging
import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, HttpUrl
import aiohttp
from urllib.parse import urljoin, urlparse
import re
import base64
from pathlib import Path

from ..core.langswarm_manager import get_langswarm_manager, LangSwarmManager
from ..core.config import get_settings
from ..core.ai_designer import AIDesigner, WebsiteAnalysis, ChatUIDesign, PersonalizedPrompt
from ..core.demo_manager import get_demo_manager, DemoManager, DemoCreationRequest, DemoMetadata, ChatDesign, DesignUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])

# Setup Jinja2 templates
templates_dir = Path(__file__).parent.parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


class WebsiteProxyRequest(BaseModel):
    """Request model for website proxy"""
    url: HttpUrl = Field(..., description="Target website URL to reproduce")
    chat_position: str = Field(default="bottom-right", description="Chat widget position")
    chat_theme: str = Field(default="light", description="Chat widget theme")
    chat_title: str = Field(default="Chat with us", description="Chat widget title")
    enable_branding: bool = Field(default=False, description="Show AAF branding")
    custom_css: Optional[str] = Field(None, description="Custom CSS for chat widget")
    use_ai_design: bool = Field(default=False, description="Use AI to auto-design UI based on website")
    use_ai_prompt: bool = Field(default=False, description="Generate personalized system prompt")


class ChatConfig(BaseModel):
    """Chat configuration for demo"""
    agent_id: Optional[str] = Field(None, description="Specific agent to use")
    session_id: Optional[str] = Field(None, description="Chat session ID")
    welcome_message: Optional[str] = Field(None, description="Welcome message")
    placeholder_text: str = Field(default="Type your message...", description="Input placeholder")
    max_height: str = Field(default="400px", description="Maximum chat height")


class WebsiteProxy:
    """Handles website content fetching and modification"""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def fetch_website(self, url: str) -> Dict[str, Any]:
        """Fetch website content and resources"""
        try:
            session = await self.get_session()
            
            # Fetch main HTML
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to fetch website: {response.status}"
                    )
                
                html_content = await response.text()
                content_type = response.headers.get('content-type', '')
                
                if 'text/html' not in content_type:
                    raise HTTPException(
                        status_code=400,
                        detail="URL does not return HTML content"
                    )
            
            # Process the HTML
            processed_html = await self.process_html(html_content, url)
            
            return {
                'html': processed_html,
                'original_url': url,
                'title': self.extract_title(html_content),
                'base_url': self.get_base_url(url)
            }
            
        except aiohttp.ClientError as e:
            logger.error(f"Failed to fetch website {url}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Unable to fetch website: {str(e)}"
            )
    
    async def process_html(self, html: str, base_url: str) -> str:
        """Process HTML to fix relative URLs and add security measures"""
        
        # Convert relative URLs to absolute
        html = self.fix_relative_urls(html, base_url)
        
        # Add security headers and sandbox
        html = self.add_security_measures(html)
        
        # Remove potentially problematic scripts
        html = self.sanitize_scripts(html)
        
        return html
    
    def fix_relative_urls(self, html: str, base_url: str) -> str:
        """Convert relative URLs to absolute URLs"""
        
        # Fix src attributes (images, scripts, etc.)
        html = re.sub(
            r'src="(?!https?://)([^"]+)"',
            lambda m: f'src="{urljoin(base_url, m.group(1))}"',
            html
        )
        
        # Fix href attributes (links, stylesheets)
        html = re.sub(
            r'href="(?!https?://)([^"]+)"',
            lambda m: f'href="{urljoin(base_url, m.group(1))}"',
            html
        )
        
        # Fix CSS url() references
        html = re.sub(
            r'url\(["\']?(?!https?://)([^"\')]+)["\']?\)',
            lambda m: f'url("{urljoin(base_url, m.group(1))}")',
            html
        )
        
        return html
    
    def add_security_measures(self, html: str) -> str:
        """Add security measures to prevent issues"""
        
        # Add base tag if not present
        if '<base' not in html.lower():
            base_tag = '<base target="_blank">'
            html = html.replace('<head>', f'<head>\n{base_tag}', 1)
        
        # Add CSP meta tag for additional security
        csp_tag = '''
        <meta http-equiv="Content-Security-Policy" content="
            default-src 'self' 'unsafe-inline' 'unsafe-eval' *;
            script-src 'self' 'unsafe-inline' 'unsafe-eval' *;
            style-src 'self' 'unsafe-inline' *;
            img-src 'self' data: *;
            frame-src 'self' *;
        ">
        '''
        html = html.replace('<head>', f'<head>\n{csp_tag}', 1)
        
        return html
    
    def sanitize_scripts(self, html: str) -> str:
        """Remove or modify potentially problematic scripts"""
        
        # Remove scripts that might interfere with our chat widget
        problematic_patterns = [
            r'<script[^>]*>.*?(?:window\.location|document\.location).*?</script>',
            r'<script[^>]*>.*?(?:parent\.location|top\.location).*?</script>',
        ]
        
        for pattern in problematic_patterns:
            html = re.sub(pattern, '', html, flags=re.DOTALL | re.IGNORECASE)
        
        return html
    
    def extract_title(self, html: str) -> str:
        """Extract page title"""
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if title_match:
            return title_match.group(1).strip()
        return "Website Demo"
    
    def get_base_url(self, url: str) -> str:
        """Get base URL for relative path resolution"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"


# Global website proxy instance
website_proxy = WebsiteProxy()

# AI Designer instance - will be initialized on first use
ai_designer = None

async def get_ai_designer() -> AIDesigner:
    """Get or create AI designer instance"""
    global ai_designer
    if ai_designer is None:
        settings = get_settings()
        ai_designer = AIDesigner(settings.openai_api_key)
    return ai_designer


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await website_proxy.close()
    if ai_designer:
        await ai_designer.close()


@router.post("/website", response_class=HTMLResponse)
async def reproduce_website_with_chat(
    request: WebsiteProxyRequest,
    chat_config: ChatConfig = ChatConfig(),
    manager: LangSwarmManager = Depends(get_langswarm_manager)
):
    """
    Reproduce a customer's website with integrated chat UI
    
    This endpoint fetches the target website, processes it for security,
    and injects a fully functional chat widget for testing.
    
    If use_ai_design=true, it will automatically analyze the website and generate
    a custom-designed chat UI that matches the brand.
    """
    try:
        # Fetch and process the website
        website_data = await website_proxy.fetch_website(str(request.url))
        
        ai_analysis = None
        ai_design = None
        ai_prompt = None
        
        # Use AI design if requested
        if request.use_ai_design or request.use_ai_prompt:
            try:
                designer = await get_ai_designer()
                ai_analysis, ai_design, ai_prompt = await designer.analyze_and_design(str(request.url))
                logger.info(f"AI analysis completed for {request.url}")
                
                # Update agent with personalized prompt if requested
                if request.use_ai_prompt and ai_prompt:
                    await update_agent_with_ai_prompt(manager, ai_prompt, chat_config)
                
            except Exception as e:
                logger.warning(f"AI design failed, using fallback: {e}")
        
        # Get chat widget HTML and CSS (using AI design if available)
        effective_request = apply_ai_design_to_request(request, ai_design) if ai_design else request
        effective_config = apply_ai_prompt_to_config(chat_config, ai_prompt) if ai_prompt else chat_config
        
        chat_widget_html = generate_chat_widget_html(effective_request, effective_config, ai_analysis)
        chat_widget_css = generate_chat_widget_css(effective_request, ai_design)
        chat_widget_js = generate_chat_widget_js(effective_config)
        
        # Inject chat widget into the website
        modified_html = inject_chat_widget(
            website_data['html'],
            chat_widget_html,
            chat_widget_css,
            chat_widget_js,
            effective_request
        )
        
        return HTMLResponse(content=modified_html)
        
    except Exception as e:
        logger.error(f"Demo website reproduction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reproduce website: {str(e)}"
        )


@router.get("/website-simple")
async def simple_website_demo(
    url: str,
    chat_position: str = "bottom-right",
    chat_theme: str = "light"
):
    """
    Simple website demo endpoint for quick testing
    """
    request_data = WebsiteProxyRequest(
        url=url,
        chat_position=chat_position,
        chat_theme=chat_theme
    )
    
    return await reproduce_website_with_chat(request_data)


@router.get("/preview", response_class=HTMLResponse)
async def chat_widget_preview():
    """
    Preview the chat widget standalone (without website integration)
    """
    preview_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AAF Chat Widget Preview</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            .preview-container {
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }
            .preview-container h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            .preview-container p {
                font-size: 1.2em;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="preview-container">
            <h1>🤖 AAF Chat Widget</h1>
            <p>This is how your chat widget will appear on your website</p>
            <p>Try clicking the chat icon in the bottom-right corner!</p>
        </div>
        
        <!-- Chat Widget will be injected here -->
    </body>
    </html>
    """
    
    # Add chat widget
    request_data = WebsiteProxyRequest(url="preview")
    chat_config = ChatConfig(welcome_message="👋 Welcome! This is a preview of your chat widget.")
    
    chat_widget_html = generate_chat_widget_html(request_data, chat_config)
    chat_widget_css = generate_chat_widget_css(request_data)
    chat_widget_js = generate_chat_widget_js(chat_config)
    
    modified_html = inject_chat_widget(
        preview_html,
        chat_widget_html,
        chat_widget_css,
        chat_widget_js,
        request_data
    )
    
    return HTMLResponse(content=modified_html)


def generate_chat_widget_html(request: WebsiteProxyRequest, config: ChatConfig, analysis: Optional[WebsiteAnalysis] = None) -> str:
    """Generate chat widget HTML with optional AI analysis"""
    
    widget_html = f"""
    <!-- AAF Chat Widget -->
    <div id="aaf-chat-widget" class="aaf-chat-{request.chat_position} aaf-chat-{request.chat_theme}">
        <!-- Chat Toggle Button -->
        <div id="aaf-chat-toggle" class="aaf-chat-toggle">
            <svg id="aaf-chat-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M20 2H4C2.9 2 2 2.9 2 4V18L6 14H20C21.1 14 22 13.1 22 12V4C22 2.9 21.1 2 20 2Z" fill="currentColor"/>
            </svg>
            <svg id="aaf-close-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" style="display: none;">
                <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12Z" fill="currentColor"/>
            </svg>
        </div>
        
        <!-- Chat Window -->
        <div id="aaf-chat-window" class="aaf-chat-window" style="display: none;">
            <!-- Chat Header -->
            <div class="aaf-chat-header">
                <div class="aaf-chat-title">{request.chat_title}</div>
                <div class="aaf-chat-status">
                    <span class="aaf-status-dot"></span>
                    Online
                </div>
            </div>
            
            <!-- Chat Messages -->
            <div id="aaf-chat-messages" class="aaf-chat-messages">
                {f'<div class="aaf-message aaf-message-bot">{config.welcome_message}</div>' if config.welcome_message else ''}
            </div>
            
            <!-- Chat Input -->
            <div class="aaf-chat-input-container">
                <div class="aaf-chat-input-wrapper">
                    <input 
                        type="text" 
                        id="aaf-chat-input" 
                        class="aaf-chat-input" 
                        placeholder="{config.placeholder_text}"
                        maxlength="500"
                    >
                    <button id="aaf-chat-send" class="aaf-chat-send-btn">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                            <path d="M2.01 21L23 12 2.01 3 2 10L17 12 2 14Z" fill="currentColor"/>
                        </svg>
                    </button>
                </div>
                <div class="aaf-chat-typing" id="aaf-chat-typing" style="display: none;">
                    <span></span><span></span><span></span>
                </div>
            </div>
            
            <!-- Chat Footer -->
            <div class="aaf-chat-footer">
                {'<div class="aaf-powered-by">Powered by AAF</div>' if request.enable_branding else ''}
            </div>
        </div>
    </div>
    """
    
    return widget_html


def generate_chat_widget_css(request: WebsiteProxyRequest, ai_design: Optional[ChatUIDesign] = None) -> str:
    """Generate chat widget CSS with optional AI design"""
    
    # Position styles
    position_styles = {
        "bottom-right": "bottom: 20px; right: 20px;",
        "bottom-left": "bottom: 20px; left: 20px;",
        "top-right": "top: 20px; right: 20px;",
        "top-left": "top: 20px; left: 20px;",
    }
    
    # Theme colors
    themes = {
        "light": {
            "primary": "#007bff",
            "secondary": "#6c757d",
            "background": "#ffffff",
            "text": "#333333",
            "border": "#e9ecef",
            "input_bg": "#f8f9fa"
        },
        "dark": {
            "primary": "#0d6efd",
            "secondary": "#6c757d",
            "background": "#2d3748",
            "text": "#ffffff",
            "border": "#4a5568",
            "input_bg": "#1a202c"
        },
        "brand": {
            "primary": "#28a745",
            "secondary": "#17a2b8",
            "background": "#ffffff",
            "text": "#333333",
            "border": "#e9ecef",
            "input_bg": "#f8f9fa"
        }
    }
    
    position_css = position_styles.get(request.chat_position, position_styles["bottom-right"])
    
    # Use AI design if available, otherwise use predefined themes
    if ai_design:
        theme = {
            "primary": ai_design.primary_color,
            "secondary": ai_design.secondary_color,
            "background": ai_design.background_color,
            "text": ai_design.text_color,
            "border": ai_design.secondary_color,
            "input_bg": ai_design.background_color,
            "font_family": ai_design.font_family,
            "border_radius": ai_design.border_radius
        }
    else:
        theme = themes.get(request.chat_theme, themes["light"])
        theme["font_family"] = "Arial, sans-serif"
        theme["border_radius"] = "12px"
    
    css = f"""
    <style>
    /* AAF Chat Widget Styles {f"- AI Generated for {ai_design.theme_name}" if ai_design else ""} */
    #aaf-chat-widget {{
        position: fixed;
        {position_css}
        z-index: 999999;
        font-family: {theme.get('font_family', 'Arial, sans-serif')};
        font-size: 14px;
        line-height: 1.4;
    }}
    
    .aaf-chat-toggle {{
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: {theme['primary']};
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
        border: none;
    }}
    
    .aaf-chat-toggle:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.3);
    }}
    
    .aaf-chat-window {{
        width: 350px;
        height: 500px;
        background: {theme['background']};
        border-radius: {theme.get('border_radius', '12px')};
        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
        display: flex;
        flex-direction: column;
        position: absolute;
        bottom: 80px;
        right: 0;
        overflow: hidden;
        animation: slideUp 0.3s ease;
        font-family: {theme.get('font_family', 'Arial, sans-serif')};
    }}
    
    @keyframes slideUp {{
        from {{ transform: translateY(20px); opacity: 0; }}
        to {{ transform: translateY(0); opacity: 1; }}
    }}
    
    .aaf-chat-header {{
        background: {theme['primary']};
        color: white;
        padding: 16px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    
    .aaf-chat-title {{
        font-weight: 600;
        font-size: 16px;
    }}
    
    .aaf-chat-status {{
        display: flex;
        align-items: center;
        font-size: 12px;
        opacity: 0.9;
    }}
    
    .aaf-status-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #00ff88;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    .aaf-chat-messages {{
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        background: {theme['background']};
        max-height: calc(500px - 140px);
    }}
    
    .aaf-message {{
        margin-bottom: 16px;
        max-width: 80%;
        padding: 12px 16px;
        border-radius: 18px;
        word-wrap: break-word;
    }}
    
    .aaf-message-user {{
        background: {theme['primary']};
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }}
    
    .aaf-message-bot {{
        background: {theme['border']};
        color: {theme['text']};
        border-bottom-left-radius: 4px;
    }}
    
    .aaf-chat-input-container {{
        padding: 16px 20px;
        border-top: 1px solid {theme['border']};
        background: {theme['background']};
    }}
    
    .aaf-chat-input-wrapper {{
        display: flex;
        align-items: center;
        background: {theme['input_bg']};
        border: 1px solid {theme['border']};
        border-radius: 24px;
        padding: 8px 12px;
    }}
    
    .aaf-chat-input {{
        flex: 1;
        border: none;
        outline: none;
        background: transparent;
        padding: 8px 12px;
        color: {theme['text']};
        font-size: 14px;
    }}
    
    .aaf-chat-input::placeholder {{
        color: {theme['secondary']};
    }}
    
    .aaf-chat-send-btn {{
        background: {theme['primary']};
        color: white;
        border: none;
        border-radius: 50%;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: background 0.2s ease;
    }}
    
    .aaf-chat-send-btn:hover {{
        background: {theme['secondary']};
    }}
    
    .aaf-chat-send-btn:disabled {{
        opacity: 0.6;
        cursor: not-allowed;
    }}
    
    .aaf-chat-typing {{
        display: flex;
        align-items: center;
        padding: 8px 16px;
        font-size: 12px;
        color: {theme['secondary']};
    }}
    
    .aaf-chat-typing span {{
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: {theme['secondary']};
        margin-right: 4px;
        animation: typing 1.4s infinite;
    }}
    
    .aaf-chat-typing span:nth-child(2) {{ animation-delay: 0.2s; }}
    .aaf-chat-typing span:nth-child(3) {{ animation-delay: 0.4s; }}
    
    @keyframes typing {{
        0%, 60%, 100% {{ transform: translateY(0); }}
        30% {{ transform: translateY(-10px); }}
    }}
    
    .aaf-chat-footer {{
        padding: 8px 20px;
        text-align: center;
        border-top: 1px solid {theme['border']};
        background: {theme['input_bg']};
    }}
    
    .aaf-powered-by {{
        font-size: 10px;
        color: {theme['secondary']};
        opacity: 0.7;
    }}
    
    /* Mobile responsiveness */
    @media (max-width: 480px) {{
        .aaf-chat-window {{
            width: calc(100vw - 40px);
            height: calc(100vh - 40px);
            bottom: 20px;
            right: 20px;
            left: 20px;
        }}
        
        #aaf-chat-widget.aaf-chat-bottom-left .aaf-chat-window,
        #aaf-chat-widget.aaf-chat-bottom-right .aaf-chat-window {{
            right: 20px;
            left: 20px;
        }}
    }}
    
    /* Custom CSS injection */
    {request.custom_css or ''}
    </style>
    """
    
    return css


def generate_chat_widget_js(config: ChatConfig) -> str:
    """Generate chat widget JavaScript"""
    
    js = f"""
    <script>
    (function() {{
        // AAF Chat Widget JavaScript
        let chatOpen = false;
        let sessionId = '{config.session_id or f"demo_{int(time.time() * 1000)}_{uuid.uuid4().hex[:9]}"}';
        let agentId = '{config.agent_id or ""}';
        
        // DOM elements
        const chatToggle = document.getElementById('aaf-chat-toggle');
        const chatWindow = document.getElementById('aaf-chat-window');
        const chatInput = document.getElementById('aaf-chat-input');
        const chatSend = document.getElementById('aaf-chat-send');
        const chatMessages = document.getElementById('aaf-chat-messages');
        const chatIcon = document.getElementById('aaf-chat-icon');
        const closeIcon = document.getElementById('aaf-close-icon');
        const typingIndicator = document.getElementById('aaf-chat-typing');
        
        // Initialize chat widget
        function initChat() {{
            chatToggle.addEventListener('click', toggleChat);
            chatSend.addEventListener('click', sendMessage);
            chatInput.addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    sendMessage();
                }}
            }});
            
            // Auto-scroll messages
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}
        
        function toggleChat() {{
            chatOpen = !chatOpen;
            
            if (chatOpen) {{
                chatWindow.style.display = 'flex';
                chatIcon.style.display = 'none';
                closeIcon.style.display = 'block';
                chatInput.focus();
            }} else {{
                chatWindow.style.display = 'none';
                chatIcon.style.display = 'block';
                closeIcon.style.display = 'none';
            }}
        }}
        
        function addMessage(content, isUser = false) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `aaf-message ${{isUser ? 'aaf-message-user' : 'aaf-message-bot'}}`;
            messageDiv.textContent = content;
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}
        
        function showTyping() {{
            typingIndicator.style.display = 'flex';
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }}
        
        function hideTyping() {{
            typingIndicator.style.display = 'none';
        }}
        
        async function sendMessage() {{
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message
            addMessage(message, true);
            chatInput.value = '';
            chatSend.disabled = true;
            
            // Show typing indicator
            showTyping();
            
            try {{
                // Send to AAF API
                const response = await fetch('/api/chat/', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        message: message,
                        session_id: sessionId,
                        agent_id: agentId || undefined
                    }})
                }});
                
                const data = await response.json();
                
                if (response.ok) {{
                    // Add bot response
                    addMessage(data.response);
                }} else {{
                    addMessage('Sorry, I encountered an error. Please try again.');
                }}
            }} catch (error) {{
                console.error('Chat error:', error);
                addMessage('Sorry, I cannot connect right now. Please try again later.');
            }} finally {{
                hideTyping();
                chatSend.disabled = false;
                chatInput.focus();
            }}
        }}
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initChat);
        }} else {{
            initChat();
        }}
        
        // Expose chat API for external use
        window.AAFChat = {{
            open: function() {{ if (!chatOpen) toggleChat(); }},
            close: function() {{ if (chatOpen) toggleChat(); }},
            sendMessage: function(msg) {{
                chatInput.value = msg;
                sendMessage();
            }},
            setSession: function(id) {{ sessionId = id; }},
            setAgent: function(id) {{ agentId = id; }}
        }};
    }})();
    </script>
    """
    
    return js


def inject_chat_widget(html: str, widget_html: str, widget_css: str, widget_js: str, request: WebsiteProxyRequest) -> str:
    """Inject chat widget into website HTML"""
    
    # Add CSS to head
    if '</head>' in html:
        html = html.replace('</head>', f'{widget_css}\n</head>')
    else:
        html = widget_css + html
    
    # Add HTML and JS before closing body tag
    widget_injection = f'{widget_html}\n{widget_js}'
    
    if '</body>' in html:
        html = html.replace('</body>', f'{widget_injection}\n</body>')
    else:
        html = html + widget_injection
    
    return html


@router.get("/embed")
async def get_embed_code(
    chat_title: str = "Chat with us",
    chat_position: str = "bottom-right",
    chat_theme: str = "light",
    enable_branding: bool = False
):
    """
    Generate embeddable JavaScript code for websites
    """
    settings = get_settings()
    
    embed_code = f"""
<!-- AAF Chat Widget Embed Code -->
<script>
(function() {{
    // Configuration
    const config = {{
        apiUrl: '{settings.app_host}:{settings.app_port}',
        chatTitle: '{chat_title}',
        chatPosition: '{chat_position}',
        chatTheme: '{chat_theme}',
        enableBranding: {str(enable_branding).lower()}
    }};
    
    // Load chat widget
    const script = document.createElement('script');
    script.src = config.apiUrl + '/demo/widget.js';
    script.onload = function() {{
        window.initAAFChat(config);
    }};
    document.head.appendChild(script);
    
    // Load chat styles
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = config.apiUrl + '/demo/widget.css';
    document.head.appendChild(link);
}})();
</script>
<!-- End AAF Chat Widget -->
    """
    
    return {
        "embed_code": embed_code,
        "instructions": {
            "1": "Copy the embed code above",
            "2": "Paste it before the closing </body> tag on your website",
            "3": "The chat widget will automatically appear on your site",
            "4": "Customize the configuration parameters as needed"
        }
    }


@router.get("/test-urls")
async def get_test_urls():
    """
    Get suggested URLs for testing the demo functionality
    """
    return {
        "test_urls": [
            "https://example.com",
            "https://httpbin.org/html",
            "https://www.wikipedia.org",
            "https://github.com",
            "https://stackoverflow.com"
        ],
        "note": "These URLs can be used to test the website reproduction feature"
    }


# ================================
# PERSISTENT DEMO ENDPOINTS
# ================================

@router.post("/create", response_model=DemoMetadata)
async def create_persistent_demo(
    request: DemoCreationRequest,
    manager: LangSwarmManager = Depends(get_langswarm_manager),
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Create a persistent demo page with shareable URL
    
    This endpoint creates the demo page, stores it persistently, and returns
    metadata including the shareable demo URL.
    """
    try:
        # AI will generate the design, so we use the request URL and basic settings
        # The detailed design will be created by AI and stored in metadata
        proxy_request = WebsiteProxyRequest(
            url=request.url,
            chat_position=request.chat_position,
            enable_branding=request.enable_branding,
            use_ai_design=request.use_ai_design,
            use_ai_prompt=request.use_ai_prompt
        )
        
        # Generate the demo HTML using existing logic
        website_data = await website_proxy.fetch_website(str(proxy_request.url))
        
        ai_analysis = None
        ai_design = None
        ai_prompt = None
        
        # Use AI design if requested
        if proxy_request.use_ai_design or proxy_request.use_ai_prompt:
            try:
                designer = await get_ai_designer()
                ai_analysis, ai_design, ai_prompt = await designer.analyze_and_design(str(proxy_request.url))
                logger.info(f"AI analysis completed for {proxy_request.url}")
                
                # Update agent with personalized prompt if requested
                if proxy_request.use_ai_prompt and ai_prompt:
                    chat_config = ChatConfig()
                    await update_agent_with_ai_prompt(manager, ai_prompt, chat_config)
                
            except Exception as e:
                logger.warning(f"AI design failed, using fallback: {e}")
        
        # Get chat widget HTML and CSS (using AI design if available)
        effective_request = apply_ai_design_to_request(proxy_request, ai_design) if ai_design else proxy_request
        effective_config = ChatConfig()
        
        chat_widget_html = generate_chat_widget_html(effective_request, effective_config, ai_analysis)
        chat_widget_css = generate_chat_widget_css(effective_request, ai_design)
        chat_widget_js = generate_chat_widget_js(effective_config)
        
        # Inject chat widget into the website
        modified_html = inject_chat_widget(
            website_data['html'],
            chat_widget_html,
            chat_widget_css,
            chat_widget_js,
            effective_request
        )
        
        # Store the demo persistently
        metadata = await demo_manager.create_demo(request, modified_html)
        
        logger.info(f"Created persistent demo {metadata.demo_id} for {request.url}")
        return metadata
        
    except Exception as e:
        logger.error(f"Failed to create persistent demo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create demo: {str(e)}"
        )


@router.get("/list", response_model=List[DemoMetadata])
async def list_demos(
    created_by: Optional[str] = None,
    limit: int = 50,
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    List stored demo pages
    
    Optionally filter by creator and limit results.
    """
    try:
        demos = await demo_manager.list_demos(created_by=created_by, limit=limit)
        return demos
        
    except Exception as e:
        logger.error(f"Failed to list demos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list demos: {str(e)}"
        )


@router.get("/view/{demo_id}", response_class=HTMLResponse)
async def view_demo(
    demo_id: str,
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    View a stored demo page by its ID
    
    This is the shareable URL that users can access directly in their browser.
    """
    try:
        # Get demo metadata
        metadata = await demo_manager.get_demo(demo_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        # Check if demo is active and not expired
        if metadata.status != "active":
            raise HTTPException(status_code=410, detail="Demo is no longer available")
        
        # Check expiration only if expires_at is set
        if metadata.expires_at:
            if metadata.expires_at < datetime.utcnow():
                raise HTTPException(status_code=410, detail="Demo has expired")
        
        # Get HTML content
        html_content = await demo_manager.get_demo_html(demo_id)
        if not html_content:
            raise HTTPException(status_code=404, detail="Demo content not found")
        
        # Increment view count
        await demo_manager.increment_view_count(demo_id)
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to view demo {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load demo: {str(e)}"
        )


@router.get("/info/{demo_id}", response_model=DemoMetadata)
async def get_demo_info(
    demo_id: str,
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Get demo metadata without viewing the content
    """
    try:
        metadata = await demo_manager.get_demo(demo_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demo info {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get demo info: {str(e)}"
        )


@router.put("/update/{demo_id}", response_model=DemoMetadata)
async def update_demo(
    demo_id: str,
    request: DemoCreationRequest,
    manager: LangSwarmManager = Depends(get_langswarm_manager),
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Update an existing demo with new design parameters
    
    This regenerates the demo with updated settings and preserves analytics.
    """
    try:
        # Check if demo exists
        existing_metadata = await demo_manager.get_demo(demo_id)
        if not existing_metadata:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        # Generate updated demo HTML using the same logic as create
        proxy_request = WebsiteProxyRequest(
            url=request.url,
            chat_position=request.chat_position,
            chat_theme=request.chat_theme,
            chat_title=request.chat_title,
            enable_branding=request.enable_branding,
            custom_css=request.custom_css,
            use_ai_design=request.use_ai_design,
            use_ai_prompt=request.use_ai_prompt
        )
        
        # Generate the updated demo HTML
        website_data = await website_proxy.fetch_website(str(proxy_request.url))
        
        ai_analysis = None
        ai_design = None
        ai_prompt = None
        
        # Use AI design if requested
        if proxy_request.use_ai_design or proxy_request.use_ai_prompt:
            try:
                designer = await get_ai_designer()
                ai_analysis, ai_design, ai_prompt = await designer.analyze_and_design(str(proxy_request.url))
                logger.info(f"AI analysis completed for {proxy_request.url}")
                
                if proxy_request.use_ai_prompt and ai_prompt:
                    chat_config = ChatConfig()
                    await update_agent_with_ai_prompt(manager, ai_prompt, chat_config)
                
            except Exception as e:
                logger.warning(f"AI design failed, using fallback: {e}")
        
        # Generate updated chat widget
        effective_request = apply_ai_design_to_request(proxy_request, ai_design) if ai_design else proxy_request
        effective_config = ChatConfig()
        
        chat_widget_html = generate_chat_widget_html(effective_request, effective_config, ai_analysis)
        chat_widget_css = generate_chat_widget_css(effective_request, ai_design)
        chat_widget_js = generate_chat_widget_js(effective_config)
        
        # Inject updated chat widget
        modified_html = inject_chat_widget(
            website_data['html'],
            chat_widget_html,
            chat_widget_css,
            chat_widget_js,
            effective_request
        )
        
        # Update HTML content in storage
        await demo_manager._store_html_content(demo_id, modified_html)
        
        # Update metadata with new configuration
        updated_title = request.title or existing_metadata.title
        
        doc_ref = demo_manager.db.collection(demo_manager.demos_collection).document(demo_id)
        doc_ref.update({
            "title": updated_title,
            "source_url": request.url,
            "chat_config": {
                # All the design parameters
                "chat_position": request.chat_position,
                "chat_theme": request.chat_theme,
                "chat_title": request.chat_title,
                "chat_subtitle": request.chat_subtitle,
                "chat_placeholder": request.chat_placeholder,
                "primary_color": request.primary_color,
                "secondary_color": request.secondary_color,
                "text_color": request.text_color,
                "background_color": request.background_color,
                "border_radius": request.border_radius,
                "font_family": request.font_family,
                "auto_open": request.auto_open,
                "show_launcher": request.show_launcher,
                "enable_sound": request.enable_sound,
                "enable_typing_indicator": request.enable_typing_indicator,
                "enable_branding": request.enable_branding,
                "custom_css": request.custom_css,
                "custom_logo_url": request.custom_logo_url,
                "use_ai_design": request.use_ai_design,
                "use_ai_prompt": request.use_ai_prompt,
                "widget_width": request.widget_width,
                "widget_height": request.widget_height,
                "max_height": request.max_height,
                "enable_file_upload": request.enable_file_upload,
                "enable_emoji_picker": request.enable_emoji_picker,
                "enable_markdown": request.enable_markdown,
                "tags": request.tags
            },
            "updated_at": datetime.utcnow()
        })
        
        # Get updated metadata
        updated_metadata = await demo_manager.get_demo(demo_id)
        
        logger.info(f"Updated demo {demo_id} with new design parameters")
        return updated_metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update demo {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update demo: {str(e)}"
        )


@router.delete("/delete/{demo_id}")
async def delete_demo(
    demo_id: str,
    permanent: bool = False,
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Delete a demo page
    
    By default performs soft delete (marks as deleted).
    Set permanent=true for hard delete (removes from storage).
    """
    try:
        if permanent:
            # Hard delete - remove from storage completely
            success = await demo_manager.hard_delete_demo(demo_id)
            message = f"Demo {demo_id} permanently deleted"
        else:
            # Soft delete - mark as deleted
            success = await demo_manager.delete_demo(demo_id)
            message = f"Demo {demo_id} deleted (soft delete)"
        
        if not success:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        return {"message": message, "permanent": permanent}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete demo {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete demo: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_expired_demos(
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Clean up expired demo pages (admin endpoint)
    """
    try:
        deleted_count = await demo_manager.cleanup_expired_demos()
        return {
            "message": f"Cleanup completed",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup demos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup demos: {str(e)}"
        )


# ================================
# DESIGN EDITOR ENDPOINTS
# ================================

@router.get("/design/{demo_id}", response_model=ChatDesign)
async def get_demo_design(
    demo_id: str,
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Get the current design configuration for a demo
    
    Frontend uses this to load the design into the editor.
    """
    try:
        metadata = await demo_manager.get_demo(demo_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        return metadata.design
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demo design {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get demo design: {str(e)}"
        )


@router.put("/design/{demo_id}", response_model=DemoMetadata)
async def update_demo_design(
    demo_id: str,
    request: DesignUpdateRequest,
    manager: LangSwarmManager = Depends(get_langswarm_manager),
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Update demo design configuration (Frontend Design Editor)
    
    This updates the design and regenerates the HTML with new styling.
    The design persists across instance restarts via Firestore.
    """
    try:
        # Check if demo exists
        existing_metadata = await demo_manager.get_demo(demo_id)
        if not existing_metadata:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        # Update design in persistent storage
        success = await demo_manager.update_demo_design(
            demo_id, 
            request.design, 
            request.update_reason
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update design")
        
        # Regenerate HTML with new design
        # Convert design to WebsiteProxyRequest format for HTML generation
        proxy_request = WebsiteProxyRequest(
            url=existing_metadata.source_url,
            chat_position=request.design.chat_position,
            chat_theme=request.design.chat_theme,
            chat_title=request.design.chat_title,
            enable_branding=request.design.enable_branding,
            custom_css=request.design.custom_css,
            use_ai_design=False,  # Design already provided
            use_ai_prompt=False
        )
        
        # Generate updated HTML
        website_data = await website_proxy.fetch_website(existing_metadata.source_url)
        
        # Create ChatConfig from design
        chat_config = ChatConfig(
            placeholder=request.design.chat_placeholder,
            max_height=request.design.max_height
        )
        
        chat_widget_html = generate_chat_widget_html(proxy_request, chat_config, None)
        chat_widget_css = generate_chat_widget_css(proxy_request, None)
        chat_widget_js = generate_chat_widget_js(chat_config)
        
        # Inject updated chat widget
        modified_html = inject_chat_widget(
            website_data['html'],
            chat_widget_html,
            chat_widget_css,
            chat_widget_js,
            proxy_request
        )
        
        # Update HTML content in storage
        await demo_manager._store_html_content(demo_id, modified_html)
        
        # Get updated metadata
        updated_metadata = await demo_manager.get_demo(demo_id)
        
        logger.info(f"Updated design for demo {demo_id} via frontend editor")
        return updated_metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update demo design {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update design: {str(e)}"
        )


@router.post("/design/{demo_id}/reset")
async def reset_demo_design(
    demo_id: str,
    design_preference: str = "professional",
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Reset demo design to AI-generated baseline
    
    Useful for starting over with AI design after manual edits.
    """
    try:
        metadata = await demo_manager.get_demo(demo_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Demo not found")
        
        # Generate fresh AI design
        new_ai_design = await demo_manager.generate_ai_design(
            metadata.source_url, 
            design_preference
        )
        
        # Update design
        success = await demo_manager.update_demo_design(
            demo_id, 
            new_ai_design, 
            f"Reset to AI design ({design_preference})"
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset design")
        
        return {
            "message": f"Design reset to AI baseline ({design_preference})",
            "design": new_ai_design
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset demo design {demo_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset design: {str(e)}"
        )


@router.get("/debug/firestore")
async def debug_firestore(
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Debug endpoint to check Firestore collections and documents
    """
    try:
        # Get Firestore client
        db = demo_manager.db
        
        # Check demos collection
        demos_collection = demo_manager.demos_collection
        demos_ref = db.collection(demos_collection)
        
        # Get all docs (no filters)
        all_docs = list(demos_ref.stream())
        
        debug_info = {
            "firestore_connected": True,
            "demos_collection": demos_collection,
            "total_documents": len(all_docs),
            "documents": []
        }
        
        for doc in all_docs:
            doc_data = doc.to_dict()
            debug_info["documents"].append({
                "doc_id": doc.id,
                "demo_id": doc_data.get("demo_id", "N/A"),
                "title": doc_data.get("title", "N/A"),
                "created_by": doc_data.get("created_by", "N/A"),
                "status": doc_data.get("status", "N/A"),
                "created_at": str(doc_data.get("created_at", "N/A"))
            })
        
        return debug_info
        
    except Exception as e:
        return {
            "firestore_connected": False,
            "error": str(e),
            "demos_collection": getattr(demo_manager, 'demos_collection', 'unknown'),
            "total_documents": 0,
            "documents": []
        }


@router.get("/debug/find/{demo_id}")
async def debug_find_demo(
    demo_id: str,
    demo_manager: DemoManager = Depends(get_demo_manager)
):
    """
    Debug endpoint to find a specific demo by ID
    """
    try:
        # Direct Firestore query
        db = demo_manager.db
        demos_ref = db.collection(demo_manager.demos_collection)
        
        # Search by demo_id field
        query = demos_ref.where("demo_id", "==", demo_id)
        docs = list(query.stream())
        
        # Also search by document ID
        doc_by_id = demos_ref.document(demo_id).get()
        
        return {
            "demo_id": demo_id,
            "found_by_field": len(docs) > 0,
            "found_by_doc_id": doc_by_id.exists,
            "field_search_results": [
                {
                    "doc_id": doc.id,
                    "data": doc.to_dict()
                } for doc in docs
            ],
            "doc_id_search": {
                "exists": doc_by_id.exists,
                "data": doc_by_id.to_dict() if doc_by_id.exists else None
            }
        }
        
    except Exception as e:
        return {
            "demo_id": demo_id,
            "error": str(e),
            "found_by_field": False,
            "found_by_doc_id": False
        }


@router.post("/ai-analyze")
async def analyze_website_with_ai(url: str):
    """
    Analyze a website with AI and return design suggestions and company information
    """
    try:
        designer = await get_ai_designer()
        analysis, design, prompt = await designer.analyze_and_design(url)
        
        return {
            "analysis": {
                "company_name": analysis.company_name,
                "industry": analysis.industry,
                "business_type": analysis.business_type,
                "language": analysis.language,
                "country": analysis.country,
                "design_style": analysis.design_style,
                "tone": analysis.tone,
                "target_audience": analysis.target_audience,
                "primary_colors": analysis.primary_colors,
                "services": analysis.services,
                "main_topics": analysis.main_topics
            },
            "design": {
                "primary_color": design.primary_color,
                "secondary_color": design.secondary_color,
                "background_color": design.background_color,
                "text_color": design.text_color,
                "accent_color": design.accent_color,
                "font_family": design.font_family,
                "border_radius": design.border_radius,
                "chat_position": design.chat_position,
                "theme_name": design.theme_name,
                "chat_title": design.chat_title,
                "welcome_message": design.welcome_message,
                "placeholder_text": design.placeholder_text
            },
            "prompt": {
                "system_prompt": prompt.system_prompt,
                "agent_name": prompt.agent_name,
                "agent_role": prompt.agent_role,
                "company_context": prompt.company_context,
                "language": prompt.language
            }
        }
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(e)}"
        )


async def update_agent_with_ai_prompt(manager: LangSwarmManager, ai_prompt: PersonalizedPrompt, chat_config: ChatConfig):
    """Update agent configuration with AI-generated prompt"""
    try:
        # Create a temporary agent configuration with the AI prompt
        temp_agent_config = {
            "id": f"ai_agent_{chat_config.agent_id or 'demo'}",
            "model": "gpt-4",
            "system_prompt": ai_prompt.system_prompt,
            "behavior": "helpful",
            "language": ai_prompt.language,
            "role": ai_prompt.agent_role
        }
        
        # Update the chat config to use this agent
        if not chat_config.agent_id:
            chat_config.agent_id = temp_agent_config["id"]
        
        logger.info(f"Updated agent with AI-generated prompt for {ai_prompt.language} language")
        
    except Exception as e:
        logger.error(f"Failed to update agent with AI prompt: {e}")


def apply_ai_design_to_request(request: WebsiteProxyRequest, ai_design: ChatUIDesign) -> WebsiteProxyRequest:
    """Apply AI design to the request"""
    if not ai_design:
        return request
    
    # Create new request with AI design applied
    updated_request = request.copy()
    updated_request.chat_position = ai_design.chat_position
    updated_request.chat_theme = ai_design.theme_name
    updated_request.chat_title = ai_design.chat_title
    updated_request.custom_css = ai_design.custom_css
    
    return updated_request


def apply_ai_prompt_to_config(chat_config: ChatConfig, ai_prompt: PersonalizedPrompt) -> ChatConfig:
    """Apply AI prompt to chat config"""
    if not ai_prompt:
        return chat_config
    
    # Create new config with AI prompt applied
    updated_config = chat_config.copy()
    updated_config.welcome_message = ai_prompt.system_prompt.split('\n')[0]  # Use first line as welcome
    updated_config.placeholder_text = f"Message {ai_prompt.agent_name}..."
    
    return updated_config


