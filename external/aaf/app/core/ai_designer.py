"""
AI-Powered Chat UI Designer
Automatically designs chat UI based on website analysis and generates personalized prompts
"""
import logging
import asyncio
import re
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import aiohttp
from bs4 import BeautifulSoup
import colorsys
from langswarm.core.base.bot import LLM

logger = logging.getLogger(__name__)


@dataclass
class WebsiteAnalysis:
    """Website analysis results"""
    # Visual Design
    primary_colors: List[str]
    secondary_colors: List[str]
    text_colors: List[str]
    background_colors: List[str]
    font_families: List[str]
    design_style: str  # modern, traditional, minimal, bold, etc.
    
    # Company Information
    company_name: Optional[str]
    industry: Optional[str]
    business_type: Optional[str]  # e commerce, saas, consulting, etc.
    language: str
    country: Optional[str]
    
    # Content Analysis
    main_topics: List[str]
    services: List[str]
    tone: str  # professional, casual, friendly, technical, etc.
    target_audience: str  # b2b, b2c, technical, general, etc.


@dataclass
class ChatUIDesign:
    """Generated chat UI design"""
    # Colors
    primary_color: str
    secondary_color: str
    background_color: str
    text_color: str
    accent_color: str
    
    # Typography
    font_family: str
    font_size: str
    
    # Layout
    border_radius: str
    chat_position: str
    theme_name: str
    
    # Branding
    chat_title: str
    welcome_message: str
    placeholder_text: str
    
    # Custom CSS
    custom_css: str


@dataclass
class PersonalizedPrompt:
    """Generated personalized system prompt"""
    system_prompt: str
    agent_name: str
    agent_role: str
    company_context: str
    language: str


class MinimalUtils:
    """Minimal utilities class to avoid tokenizer initialization issues in containers"""
    def __init__(self):
        self.bot_logs = []
    def _get_api_key(self, provider, api_key):
        import os
        env_var_map = {
            "langchain": "OPENAI_API_KEY",
            "langchain-openai": "OPENAI_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        env_var = env_var_map.get(provider.lower())
        if env_var and (key_from_env := os.getenv(env_var)):
            return key_from_env
        if api_key:
            return api_key
        raise ValueError(f"API key for {provider} not found. Set {env_var} or pass the key explicitly.")
    def bot_log(self, bot, message):
        self.bot_logs.append((bot, message))
    def clean_text(self, text: str, remove_linebreaks: bool = False) -> str:
        import unicodedata
        if hasattr(text, '_mock_name') or not isinstance(text, str):
            return str(text)
        text = text.replace("\u00a0", " ")
        if remove_linebreaks:
            text = text.replace('\n', ' ').replace('\r', ' ')
        return unicodedata.normalize("NFKD", text)
    def safe_json_loads(self, text: str):
        import json
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return None
    def update_price_tokens_use_estimates(self, *args, **kwargs):
        """Stub method for token usage tracking - no-op in minimal utils"""
        pass


class AIDesigner:
    """AI-powered chat UI designer and prompt generator"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.session = None
        
        # Create minimal utils instance for LLM
        minimal_utils = MinimalUtils()
        
        # Initialize LangSwarm agent for design analysis
        self.design_agent = LLM(
            name="design_analyzer",
            model="gpt-4",
            provider="openai",
            api_key=openai_api_key,
            system_prompt=self._get_design_analysis_prompt(),
            temperature=0.7,
            verbose=False,
            utils=minimal_utils
        )
        
        # Initialize agent for prompt generation
        self.prompt_agent = LLM(
            name="prompt_generator", 
            model="gpt-4",
            provider="openai",
            api_key=openai_api_key,
            system_prompt=self._get_prompt_generation_prompt(),
            temperature=0.7,
            verbose=False,
            utils=minimal_utils
        )
    
    async def get_session(self):
        """Get aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def analyze_and_design(self, url: str) -> Tuple[WebsiteAnalysis, ChatUIDesign, PersonalizedPrompt]:
        """Complete website analysis and design generation"""
        try:
            # Step 1: Analyze website
            logger.info(f"Starting AI analysis of website: {url}")
            website_analysis = await self.analyze_website(url)
            
            # Step 2: Generate chat UI design
            logger.info("Generating chat UI design based on analysis")
            ui_design = await self.generate_ui_design(website_analysis)
            
            # Step 3: Generate personalized prompt
            logger.info("Creating personalized system prompt")
            personalized_prompt = await self.generate_personalized_prompt(website_analysis)
            
            logger.info("AI design generation completed successfully")
            return website_analysis, ui_design, personalized_prompt
            
        except Exception as e:
            logger.error(f"AI design generation failed: {e}")
            # Return fallback design
            return self._get_fallback_analysis(url), self._get_fallback_design(), self._get_fallback_prompt()
    
    async def analyze_website(self, url: str) -> WebsiteAnalysis:
        """Analyze website content and design"""
        try:
            # Fetch website content
            website_content = await self._fetch_website_content(url)
            
            # Extract visual elements
            visual_data = self._extract_visual_elements(website_content['html'])
            
            # Prepare analysis prompt
            analysis_input = {
                "url": url,
                "html_content": website_content['html'][:10000],  # Limit content size
                "title": website_content.get('title', ''),
                "meta_description": website_content.get('meta_description', ''),
                "visual_data": visual_data
            }
            
            # Get AI analysis
            analysis_prompt = self._create_website_analysis_prompt(analysis_input)
            response = self.design_agent.chat(analysis_prompt)
            
            # Parse AI response
            return self._parse_analysis_response(response)
            
        except Exception as e:
            logger.error(f"Website analysis failed: {e}")
            return self._get_fallback_analysis(url)
    
    async def generate_ui_design(self, analysis: WebsiteAnalysis) -> ChatUIDesign:
        """Generate chat UI design based on website analysis"""
        try:
            design_prompt = self._create_ui_design_prompt(analysis)
            response = self.design_agent.chat(design_prompt)
            
            return self._parse_design_response(response, analysis)
            
        except Exception as e:
            logger.error(f"UI design generation failed: {e}")
            return self._get_fallback_design()
    
    async def generate_personalized_prompt(self, analysis: WebsiteAnalysis) -> PersonalizedPrompt:
        """Generate personalized system prompt"""
        try:
            prompt_generation_input = self._create_prompt_generation_input(analysis)
            response = self.prompt_agent.chat(prompt_generation_input)
            
            return self._parse_prompt_response(response, analysis)
            
        except Exception as e:
            logger.error(f"Prompt generation failed: {e}")
            return self._get_fallback_prompt()
    
    async def _fetch_website_content(self, url: str) -> Dict[str, Any]:
        """Fetch and parse website content"""
        session = await self.get_session()
        
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch website: {response.status}")
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract metadata
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_desc.get('content', '') if meta_desc else ''
            
            return {
                'html': html,
                'title': title_text,
                'meta_description': meta_description,
                'domain': urlparse(url).netloc
            }
    
    def _extract_visual_elements(self, html: str) -> Dict[str, Any]:
        """Extract visual design elements from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract colors from CSS
        colors = self._extract_colors_from_css(html)
        
        # Extract fonts
        fonts = self._extract_fonts(soup)
        
        # Extract structural elements
        headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])[:10]]
        
        # Extract navigation and key sections
        nav_items = [a.get_text().strip() for a in soup.find_all('a', href=True)[:20]]
        
        return {
            'colors': colors,
            'fonts': fonts,
            'headings': headings,
            'navigation': nav_items,
            'has_header': bool(soup.find(['header', 'nav'])),
            'has_footer': bool(soup.find('footer')),
            'layout_style': self._detect_layout_style(soup)
        }
    
    def _extract_colors_from_css(self, html: str) -> List[str]:
        """Extract color values from CSS"""
        colors = []
        
        # Regex patterns for different color formats
        color_patterns = [
            r'#[0-9a-fA-F]{6}',  # Hex colors
            r'#[0-9a-fA-F]{3}',   # Short hex colors
            r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)',  # RGB colors
            r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)',  # RGBA colors
        ]
        
        for pattern in color_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            colors.extend(matches)
        
        # Remove duplicates and common defaults
        unique_colors = list(set(colors))
        filtered_colors = [c for c in unique_colors if c.lower() not in ['#000000', '#ffffff', '#000', '#fff']]
        
        return filtered_colors[:10]  # Limit to 10 colors
    
    def _extract_fonts(self, soup: BeautifulSoup) -> List[str]:
        """Extract font families from CSS and Google Fonts"""
        fonts = []
        
        # Look for Google Fonts links
        font_links = soup.find_all('link', href=re.compile(r'fonts\.googleapis\.com'))
        for link in font_links:
            href = link.get('href', '')
            # Extract font family names from Google Fonts URLs
            if 'family=' in href:
                font_part = href.split('family=')[1].split('&')[0]
                fonts.extend(font_part.replace('+', ' ').split('|'))
        
        # Look for font-family in style attributes and CSS
        font_pattern = r'font-family:\s*([^;]+)'
        style_tags = soup.find_all('style')
        for style in style_tags:
            matches = re.findall(font_pattern, style.get_text(), re.IGNORECASE)
            fonts.extend([m.strip(' "\'') for m in matches])
        
        return list(set(fonts))[:5]
    
    def _detect_layout_style(self, soup: BeautifulSoup) -> str:
        """Detect overall layout style"""
        # Simple heuristics for layout detection
        if soup.find(class_=re.compile(r'grid|flex', re.I)):
            return 'modern'
        elif soup.find('table', class_=re.compile(r'layout', re.I)):
            return 'traditional'
        elif len(soup.find_all('div')) > len(soup.find_all('section')):
            return 'div-based'
        else:
            return 'semantic'
    
    def _create_website_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for website analysis"""
        return f"""
Analyze the following website and provide a comprehensive analysis in JSON format:

URL: {data['url']}
Title: {data['title']}
Meta Description: {data['meta_description']}

Visual Elements:
- Colors found: {data['visual_data']['colors']}
- Fonts: {data['visual_data']['fonts']}
- Key headings: {data['visual_data']['headings']}
- Navigation items: {data['visual_data']['navigation']}
- Layout style: {data['visual_data']['layout_style']}

HTML Content (first 10,000 chars):
{data['html_content']}

Please analyze and return a JSON object with the following structure:
{{
  "company_name": "extracted company name",
  "industry": "industry type (e.g., technology, healthcare, retail)",
  "business_type": "business model (e.g., ecommerce, saas, consulting)",
  "language": "detected language code (e.g., en, es, fr)",
  "country": "detected country if apparent",
  "primary_colors": ["#color1", "#color2"],
  "secondary_colors": ["#color3", "#color4"],
  "design_style": "modern|traditional|minimal|bold|creative",
  "font_families": ["Font Name 1", "Font Name 2"],
  "main_topics": ["topic1", "topic2", "topic3"],
  "services": ["service1", "service2"],
  "tone": "professional|casual|friendly|technical|authoritative",
  "target_audience": "b2b|b2c|technical|general|specific_niche"
}}

Focus on extracting accurate company information and understanding the brand personality.
"""
    
    def _create_ui_design_prompt(self, analysis: WebsiteAnalysis) -> str:
        """Create prompt for UI design generation"""
        return f"""
Based on the following website analysis, design a chat UI that perfectly matches the website's brand and aesthetic:

Company: {analysis.company_name}
Industry: {analysis.industry}
Design Style: {analysis.design_style}
Tone: {analysis.tone}
Primary Colors: {analysis.primary_colors}
Secondary Colors: {analysis.secondary_colors}
Font Families: {analysis.font_families}
Target Audience: {analysis.target_audience}

Generate a chat UI design that:
1. Complements the website's color scheme
2. Matches the brand personality and tone
3. Feels native to the website
4. Optimizes for the target audience

Return a JSON object with this structure:
{{
  "primary_color": "#hexcolor - main brand color for buttons/headers",
  "secondary_color": "#hexcolor - secondary accent color", 
  "background_color": "#hexcolor - chat window background",
  "text_color": "#hexcolor - main text color",
  "accent_color": "#hexcolor - for highlights and animations",
  "font_family": "Font Name - primary font",
  "font_size": "14px - base font size",
  "border_radius": "12px - consistent border radius",
  "chat_position": "bottom-right|bottom-left - best position for this site",
  "theme_name": "custom - generated theme name",
  "chat_title": "contextual title for this company",
  "welcome_message": "personalized welcome message",
  "placeholder_text": "contextual placeholder text",
  "design_rationale": "explanation of design choices"
}}

Make the design feel like it was custom-built for this specific company and website.
"""
    
    def _create_prompt_generation_input(self, analysis: WebsiteAnalysis) -> str:
        """Create input for personalized prompt generation"""
        return f"""
Generate a personalized AI assistant system prompt for the following company:

Company Information:
- Name: {analysis.company_name}
- Industry: {analysis.industry}
- Business Type: {analysis.business_type}
- Language: {analysis.language}
- Country: {analysis.country}
- Services: {analysis.services}
- Main Topics: {analysis.main_topics}
- Tone: {analysis.tone}
- Target Audience: {analysis.target_audience}

Create a system prompt that makes the AI assistant:
1. Knowledgeable about this specific company and industry
2. Matching the company's communication tone and style
3. Helpful for the target audience
4. Contextually aware of the company's services
5. Culturally appropriate for the language/country

Return a JSON object with:
{{
  "system_prompt": "detailed system prompt for the AI assistant",
  "agent_name": "appropriate name for the assistant (in the detected language)",
  "agent_role": "specific role description (e.g., 'Customer Support Specialist', 'Sales Assistant')",
  "company_context": "brief company background for the AI to reference",
  "language": "language code",
  "sample_responses": {{
    "greeting": "natural greeting in company tone",
    "how_can_help": "how the assistant can help message",
    "escalation": "when to escalate to human support"
  }}
}}

Make the assistant feel like a genuine company representative who knows the business well.
"""
    
    def _parse_analysis_response(self, response: str) -> WebsiteAnalysis:
        """Parse AI analysis response into WebsiteAnalysis object"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            data = json.loads(json_match.group())
            
            return WebsiteAnalysis(
                primary_colors=data.get('primary_colors', ['#007bff']),
                secondary_colors=data.get('secondary_colors', ['#6c757d']),
                text_colors=data.get('text_colors', ['#333333']),
                background_colors=data.get('background_colors', ['#ffffff']),
                font_families=data.get('font_families', ['Arial', 'sans-serif']),
                design_style=data.get('design_style', 'modern'),
                company_name=data.get('company_name'),
                industry=data.get('industry'),
                business_type=data.get('business_type'),
                language=data.get('language', 'en'),
                country=data.get('country'),
                main_topics=data.get('main_topics', []),
                services=data.get('services', []),
                tone=data.get('tone', 'professional'),
                target_audience=data.get('target_audience', 'general')
            )
            
        except Exception as e:
            logger.error(f"Failed to parse analysis response: {e}")
            raise
    
    def _parse_design_response(self, response: str, analysis: WebsiteAnalysis) -> ChatUIDesign:
        """Parse UI design response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in design response")
            
            data = json.loads(json_match.group())
            
            # Generate custom CSS based on the design
            custom_css = self._generate_custom_css(data, analysis)
            
            return ChatUIDesign(
                primary_color=data.get('primary_color', '#007bff'),
                secondary_color=data.get('secondary_color', '#6c757d'),
                background_color=data.get('background_color', '#ffffff'),
                text_color=data.get('text_color', '#333333'),
                accent_color=data.get('accent_color', '#17a2b8'),
                font_family=data.get('font_family', 'Arial, sans-serif'),
                font_size=data.get('font_size', '14px'),
                border_radius=data.get('border_radius', '12px'),
                chat_position=data.get('chat_position', 'bottom-right'),
                theme_name=data.get('theme_name', 'custom'),
                chat_title=data.get('chat_title', 'Chat with us'),
                welcome_message=data.get('welcome_message', 'Hello! How can I help you today?'),
                placeholder_text=data.get('placeholder_text', 'Type your message...'),
                custom_css=custom_css
            )
            
        except Exception as e:
            logger.error(f"Failed to parse design response: {e}")
            raise
    
    def _parse_prompt_response(self, response: str, analysis: WebsiteAnalysis) -> PersonalizedPrompt:
        """Parse personalized prompt response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in prompt response")
            
            data = json.loads(json_match.group())
            
            return PersonalizedPrompt(
                system_prompt=data.get('system_prompt', self._get_default_system_prompt()),
                agent_name=data.get('agent_name', 'Assistant'),
                agent_role=data.get('agent_role', 'Customer Support'),
                company_context=data.get('company_context', ''),
                language=data.get('language', analysis.language)
            )
            
        except Exception as e:
            logger.error(f"Failed to parse prompt response: {e}")
            raise
    
    def _generate_custom_css(self, design_data: Dict[str, Any], analysis: WebsiteAnalysis) -> str:
        """Generate custom CSS based on design data"""
        primary = design_data.get('primary_color', '#007bff')
        secondary = design_data.get('secondary_color', '#6c757d')
        background = design_data.get('background_color', '#ffffff')
        text = design_data.get('text_color', '#333333')
        accent = design_data.get('accent_color', '#17a2b8')
        font = design_data.get('font_family', 'Arial, sans-serif')
        radius = design_data.get('border_radius', '12px')
        
        # Generate gradient for modern designs
        if analysis.design_style == 'modern':
            gradient = self._generate_gradient(primary, accent)
        else:
            gradient = primary
        
        return f"""
/* AI-Generated Custom Theme for {analysis.company_name or 'Website'} */
.aaf-chat-toggle {{
    background: {gradient} !important;
    font-family: {font} !important;
    border-radius: 50% !important;
    box-shadow: 0 4px 20px rgba({self._hex_to_rgb(primary)}, 0.3) !important;
}}

.aaf-chat-toggle:hover {{
    transform: scale(1.1) !important;
    box-shadow: 0 6px 24px rgba({self._hex_to_rgb(primary)}, 0.4) !important;
}}

.aaf-chat-window {{
    font-family: {font} !important;
    border-radius: {radius} !important;
    background: {background} !important;
    border: 1px solid rgba({self._hex_to_rgb(secondary)}, 0.2) !important;
}}

.aaf-chat-header {{
    background: {gradient} !important;
    border-radius: {radius} {radius} 0 0 !important;
    font-family: {font} !important;
}}

.aaf-chat-title {{
    font-weight: 600 !important;
    font-size: 16px !important;
}}

.aaf-message-user {{
    background: {primary} !important;
    border-radius: {radius} {radius} 4px {radius} !important;
}}

.aaf-message-bot {{
    background: rgba({self._hex_to_rgb(secondary)}, 0.1) !important;
    color: {text} !important;
    border-radius: {radius} {radius} {radius} 4px !important;
}}

.aaf-chat-input-wrapper {{
    border-radius: calc({radius} * 2) !important;
    border: 2px solid rgba({self._hex_to_rgb(primary)}, 0.2) !important;
}}

.aaf-chat-input-wrapper:focus-within {{
    border-color: {primary} !important;
    box-shadow: 0 0 0 3px rgba({self._hex_to_rgb(primary)}, 0.1) !important;
}}

.aaf-chat-send-btn {{
    background: {accent} !important;
    border-radius: 50% !important;
}}

.aaf-chat-send-btn:hover {{
    background: {primary} !important;
}}

.aaf-status-dot {{
    background: {accent} !important;
}}

/* Custom brand styling */
.aaf-chat-messages {{
    color: {text} !important;
}}

.aaf-chat-input {{
    font-family: {font} !important;
    color: {text} !important;
}}

/* Responsive design enhancements */
@media (max-width: 768px) {{
    .aaf-chat-window {{
        border-radius: {radius} {radius} 0 0 !important;
    }}
}}
"""
    
    def _generate_gradient(self, color1: str, color2: str) -> str:
        """Generate CSS gradient"""
        return f"linear-gradient(135deg, {color1} 0%, {color2} 100%)"
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color to RGB values"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        except ValueError:
            return "0, 123, 255"  # Default blue
    
    def _get_design_analysis_prompt(self) -> str:
        """System prompt for design analysis agent"""
        return """
You are an expert web designer and brand analyst. Your job is to analyze websites and extract:

1. Visual design elements (colors, fonts, layout style)
2. Company information (name, industry, business type)
3. Brand personality and tone
4. Target audience and language
5. Services and main topics

Always respond with valid JSON format. Be precise with color extraction and accurate with company identification.
Focus on understanding the brand's visual identity and communication style.
"""
    
    def _get_prompt_generation_prompt(self) -> str:
        """System prompt for prompt generation agent"""
        return """
You are an expert AI prompt engineer specializing in creating personalized customer service and sales assistant prompts.

Your job is to create system prompts that make AI assistants feel like genuine company representatives who:
- Know the company's business, services, and industry well
- Communicate in the company's brand tone and style
- Are helpful and knowledgeable for the target audience
- Can handle common inquiries about the company
- Know when to escalate to human support

Always respond with valid JSON format. Make prompts specific to the company and industry.
"""
    
    def _get_default_system_prompt(self) -> str:
        """Default system prompt fallback"""
        return """
You are a helpful AI assistant for this website. You're knowledgeable, friendly, and professional. 
You can answer questions about the company, its services, and provide general assistance.
If you can't answer a specific question, politely let the user know and offer to connect them with a human representative.
"""
    
    def _get_fallback_analysis(self, url: str) -> WebsiteAnalysis:
        """Fallback analysis when AI analysis fails"""
        domain = urlparse(url).netloc
        company_name = domain.replace('www.', '').split('.')[0].title()
        
        return WebsiteAnalysis(
            primary_colors=['#007bff'],
            secondary_colors=['#6c757d'],
            text_colors=['#333333'],
            background_colors=['#ffffff'],
            font_families=['Arial', 'sans-serif'],
            design_style='modern',
            company_name=company_name,
            industry='General',
            business_type='website',
            language='en',
            country=None,
            main_topics=['information', 'services'],
            services=['customer support'],
            tone='professional',
            target_audience='general'
        )
    
    def _get_fallback_design(self) -> ChatUIDesign:
        """Fallback design when generation fails"""
        return ChatUIDesign(
            primary_color='#007bff',
            secondary_color='#6c757d',
            background_color='#ffffff',
            text_color='#333333',
            accent_color='#17a2b8',
            font_family='Arial, sans-serif',
            font_size='14px',
            border_radius='12px',
            chat_position='bottom-right',
            theme_name='default',
            chat_title='Chat with us',
            welcome_message='Hello! How can I help you today?',
            placeholder_text='Type your message...',
            custom_css=''
        )
    
    def _get_fallback_prompt(self) -> PersonalizedPrompt:
        """Fallback prompt when generation fails"""
        return PersonalizedPrompt(
            system_prompt=self._get_default_system_prompt(),
            agent_name='Assistant',
            agent_role='Customer Support',
            company_context='General website assistant',
            language='en'
        )
