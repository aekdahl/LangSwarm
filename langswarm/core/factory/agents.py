from typing import Any, Optional

from ..wrappers.generic import AgentWrapper
from ..utils.utilities import Utils
from ..registry.agents import AgentRegistry
from ..config import LangSwarmConfigLoader, AgentConfig

try:
    from langswarm.cortex.react.agent import ReActAgent
except ImportError:
    ReActAgent = None

try:
    from llama_index import GPTSimpleVectorIndex, Document
except ImportError:
    GPTSimpleVectorIndex = None
    Document = None

class AgentFactory:
    """
    A factory for creating LangSwarm agents, including LangChain, Hugging Face, OpenAI, and LlamaIndex agents.
    Now with simplified zero-config agent creation using behavior-driven prompts.
    """

    @staticmethod
    def create(
        name: str,
        agent_type: str,
        documents: Optional[list] = None,
        memory: Optional[Any] = None,
        langsmith_api_key: Optional[str] = None,
        register_as="agent",
        **kwargs,
    ) -> AgentWrapper:
        """
        Create an agent with the given parameters.

        Parameters:
        - name (str): The name of the agent.
        - agent_type (str): The type of agent ("langchain", "huggingface", "openai", "llamaindex", etc.).
        - documents (list, optional): Documents for LlamaIndex agents.
        - memory (optional): A memory instance to use with the agent.
        - langsmith_api_key (str, optional): API key for LangSmith logging.
        - kwargs: Additional parameters for the agent.

        Returns:
        - AgentWrapper: A wrapped agent ready for use.
        """
        agent = AgentFactory._create_base_agent(agent_type, documents, **kwargs)

        # Wrap the agent using AgentWrapper
        wrapped_agent = AgentWrapper(
            name=name,
            agent=agent,
            memory=memory,
            agent_type=agent_type,
            langsmith_api_key=langsmith_api_key,
            **kwargs,
        )
        
        # Register the agent
        AgentFactory._register_agent(wrapped_agent, register_as=register_as)
        
        return wrapped_agent
    
    # ========== ZERO-CONFIG AGENT CREATION ==========
    
    @staticmethod
    def create_simple(
        name: str,
        behavior: str = "helpful",
        model: str = "gpt-4o",
        tools: Optional[list] = None,
        memory: Optional[Any] = None,
        **kwargs
    ) -> AgentWrapper:
        """
        Create a simple agent using behavior-driven configuration.
        
        Args:
            name: Agent name and identifier
            behavior: Behavior preset (helpful, coding, research, creative, analytical, support, conversational, educational)
            model: LLM model to use
            tools: List of tool names to enable
            memory: Memory configuration
            **kwargs: Additional agent options
            
        Returns:
            AgentWrapper: Ready-to-use agent
            
        Example:
            # Create a coding assistant in one line
            agent = AgentFactory.create_simple(
                name="code_helper",
                behavior="coding",
                tools=["filesystem", "github"]
            )
        """
        # Create config loader to generate agent configuration
        config_loader = LangSwarmConfigLoader()
        
        # Generate agent config using zero-config system
        agent_config = config_loader.create_simple_agent(
            agent_id=name,
            behavior=behavior,
            model=model,
            tools=tools or [],
            memory=memory is not None,
            **kwargs
        )
        
        # Create base agent
        agent = AgentFactory._create_base_agent("openai", documents=None, model=model, **kwargs)
        
        # Create wrapper with generated system prompt
        wrapped_agent = AgentWrapper(
            name=name,
            agent=agent,
            model=model,
            system_prompt=agent_config.system_prompt,
            memory=memory,
            agent_type="generic",
            **kwargs
        )
        
        # Register the agent
        AgentFactory._register_agent(wrapped_agent, register_as="agent")
        
        return wrapped_agent
    
    @staticmethod
    def create_coding_assistant(
        name: str = "coding_assistant",
        model: str = "gpt-4o",
        tools: Optional[list] = None,
        memory: Optional[Any] = None,
        **kwargs
    ) -> AgentWrapper:
        """
        Create a specialized coding assistant with pre-configured tools and behavior.
        
        Args:
            name: Agent identifier
            model: LLM model (optimized for coding)
            tools: Additional tools beyond filesystem and github
            memory: Memory configuration
            **kwargs: Additional options
            
        Returns:
            AgentWrapper: Coding assistant ready for development tasks
        """
        default_tools = ["filesystem", "github"]
        all_tools = list(dict.fromkeys(default_tools + (tools or [])))
        
        return AgentFactory.create_simple(
            name=name,
            behavior="coding",
            model=model,
            tools=all_tools,
            memory=memory,
            **kwargs
        )
    
    @staticmethod
    def create_research_assistant(
        name: str = "research_assistant",
        model: str = "gpt-4o",
        tools: Optional[list] = None,
        memory: Optional[Any] = None,
        **kwargs
    ) -> AgentWrapper:
        """
        Create a research assistant with analysis and search capabilities.
        
        Args:
            name: Agent identifier
            model: LLM model (optimized for analysis)
            tools: Additional tools beyond web_search and filesystem
            memory: Memory configuration
            **kwargs: Additional options
            
        Returns:
            AgentWrapper: Research assistant ready for information gathering
        """
        default_tools = ["web_search", "filesystem"]
        all_tools = list(dict.fromkeys(default_tools + (tools or [])))
        
        return AgentFactory.create_simple(
            name=name,
            behavior="research",
            model=model,
            tools=all_tools,
            memory=memory,
            **kwargs
        )
    
    @staticmethod
    def create_support_agent(
        name: str = "support_agent",
        model: str = "gpt-4o-mini",
        tools: Optional[list] = None,
        memory: Optional[Any] = None,
        **kwargs
    ) -> AgentWrapper:
        """
        Create a customer support agent with helpful interactive tools.
        
        Args:
            name: Agent identifier
            model: LLM model (cost-optimized for support)
            tools: Additional tools beyond dynamic-forms and filesystem
            memory: Memory configuration
            **kwargs: Additional options
            
        Returns:
            AgentWrapper: Support agent ready for customer assistance
        """
        default_tools = ["dynamic-forms", "filesystem"]
        all_tools = list(dict.fromkeys(default_tools + (tools or [])))
        
        return AgentFactory.create_simple(
            name=name,
            behavior="support",
            model=model,
            tools=all_tools,
            memory=memory,
            **kwargs
        )
    
    @staticmethod
    def create_conversational_agent(
        name: str = "chat_agent",
        model: str = "gpt-4o-mini",
        tools: Optional[list] = None,
        memory: Optional[Any] = None,
        **kwargs
    ) -> AgentWrapper:
        """
        Create a conversational agent optimized for natural dialogue.
        
        Args:
            name: Agent identifier
            model: LLM model (optimized for responsiveness)
            tools: Tools to enable (minimal by default)
            memory: Memory configuration
            **kwargs: Additional options
            
        Returns:
            AgentWrapper: Conversational agent ready for chat
        """
        return AgentFactory.create_simple(
            name=name,
            behavior="conversational",
            model=model,
            tools=tools or [],
            memory=memory,
            **kwargs
        )
    
    # ========== ORIGINAL FACTORY METHODS ==========
    
    @staticmethod
    def create_tool_agent(
        name: str,
        agent_type: str,
        documents: Optional[list] = None,
        memory: Optional[Any] = None,
        langsmith_api_key: Optional[str] = None,
        register_as="tool",
        **kwargs,
    ) -> AgentWrapper:
        """
        Create a tool agent with the given parameters.

        Parameters:
        - name (str): The name of the agent.
        - agent_type (str): The type of agent ("langchain", "huggingface", "openai", "llamaindex", etc.).
        - documents (list, optional): Documents for LlamaIndex agents.
        - memory (optional): A memory instance to use with the agent.
        - langsmith_api_key (str, optional): API key for LangSmith logging.
        - kwargs: Additional parameters for the agent.

        Returns:
        - AgentWrapper: A wrapped agent ready for use.
        """
        agent = AgentFactory._create_base_agent(agent_type, documents, **kwargs)

        # Wrap the agent using AgentWrapper
        wrapped_agent = AgentWrapper(
            name=name,
            agent=agent,
            memory=memory,
            agent_type=agent_type,
            langsmith_api_key=langsmith_api_key,
            **kwargs,
        )
        
        # Register the agent
        AgentFactory._register_agent(wrapped_agent, register_as=register_as)
        
        return wrapped_agent
    
    @staticmethod
    def create_helper_agent(
        name: str,
        agent_type: str,
        documents: Optional[list] = None,
        memory: Optional[Any] = None,
        langsmith_api_key: Optional[str] = None,
        register_as="helper",
        **kwargs,
    ) -> AgentWrapper:
        """
        Create a tool agent with the given parameters.

        Parameters:
        - name (str): The name of the agent.
        - agent_type (str): The type of agent ("langchain", "huggingface", "openai", "llamaindex", etc.).
        - documents (list, optional): Documents for LlamaIndex agents.
        - memory (optional): A memory instance to use with the agent.
        - langsmith_api_key (str, optional): API key for LangSmith logging.
        - kwargs: Additional parameters for the agent.

        Returns:
        - AgentWrapper: A wrapped agent ready for use.
        """
        agent = AgentFactory._create_base_agent(agent_type, documents, **kwargs)

        # Wrap the agent using AgentWrapper
        wrapped_agent = AgentWrapper(
            name=name,
            agent=agent,
            memory=memory,
            agent_type=agent_type,
            langsmith_api_key=langsmith_api_key,
            **kwargs,
        )
        
        # Register the agent
        AgentFactory._register_agent(wrapped_agent, register_as=register_as)
        
        return wrapped_agent
    
    @staticmethod
    def create_react(
        name: str,
        agent_type: str,
        documents: Optional[list] = None,
        memory: Optional[Any] = None,
        langsmith_api_key: Optional[str] = None,
        register_as = "react",
        **kwargs,
    ) -> ReActAgent:
        """
        Create a ReAct agent with the given parameters.

        Parameters:
        - name (str): The name of the agent.
        - agent_type (str): The type of agent ("langchain", "huggingface", "openai", "llamaindex", etc.).
        - documents (list, optional): Documents for LlamaIndex agents.
        - memory (optional): A memory instance to use with the agent.
        - langsmith_api_key (str, optional): API key for LangSmith logging.
        - kwargs: Additional parameters for the agent.

        Returns:
        - AgentWrapper: A wrapped agent ready for use.
        """
        agent = AgentFactory._create_base_agent(agent_type, documents, **kwargs)
        
        # Wrap the agent using ReActAgent
        wrapped_agent = ReActAgent(
            name=name,
            agent=agent,
            memory=memory,
            agent_type=agent_type,
            langsmith_api_key=langsmith_api_key,
            **kwargs,
        )
        
        # Register the agent
        AgentFactory._register_agent(wrapped_agent, register_as=register_as)
        
        return wrapped_agent
    
    @staticmethod
    def _register_agent(agent, register_as="agent"):
        if register_as in ["agent","react","tool"]:
            AgentRegistry.register(agent)
        elif register_as == "helper":
            AgentRegistry.register_helper_agent(agent)
        
        return None

    @staticmethod
    def _create_base_agent(agent_type, documents, **kwargs):
        agent = None
        utils = Utils()

        if agent_type.lower() == "llamaindex":
            if GPTSimpleVectorIndex is None or Document is None:
                raise ImportError("LlamaIndex is not installed. Install it with 'pip install llama-index'.")
            if not documents:
                raise ValueError("Documents must be provided to create a LlamaIndex agent.")
            doc_objects = [Document(text=doc) for doc in documents]
            agent = GPTSimpleVectorIndex(doc_objects)

        elif agent_type.lower() == "langchain-openai" or agent_type.lower() == "langchain":
            model = kwargs.get("model", "gpt-4-1106-preview")
            api_key = utils._get_api_key('langchain-openai', kwargs.get("openai_api_key"))
            
            # Use ChatOpenAI for chat models
            if model.lower().startswith("gpt-"):
                try:
                    from langchain_openai import ChatOpenAI
                except ImportError:
                    from langchain.chat_models import ChatOpenAI
                agent = ChatOpenAI(model=model, openai_api_key=api_key)
            # Use OpenAI for text models
            else:
                try:
                    from langchain_community.llms import OpenAI
                except ImportError:
                    from langchain.llms import OpenAI
                agent = OpenAI(model=model, openai_api_key=api_key)
        
        elif agent_type.lower() == "langchain-anthropic":
            model = kwargs.get("model", "claude-2")
            api_key = utils._get_api_key('langchain-anthropic', kwargs.get("anthropic_api_key"))
            
            try:
                from langchain.llms import Anthropic
            except ImportError:
                raise ImportError(
                    "Anthropic is not available. Please install it:\n"
                    "  pip install anthropic"
                )
            agent = Anthropic(model=model, api_key=api_key)
        
        elif agent_type.lower() == "langchain-cohere":
            model = kwargs.get("model", "command")
            api_key = utils._get_api_key('langchain-cohere', kwargs.get("cohere_api_key"))
            
            try:
                from langchain.llms import Cohere
            except ImportError:
                raise ImportError(
                    "Cohere is not available. Please install it:\n"
                    "  pip install cohere"
                )
            agent = Cohere(model=model, cohere_api_key=api_key)
        
        elif agent_type.lower() == "langchain-google-palm":
            model = kwargs.get("model", "models/text-bison-001")
            api_key = utils._get_api_key('langchain-google-palm', kwargs.get("google_cloud_api_key"))
            
            try:
                from langchain.llms import GooglePalm
            except ImportError:
                raise ImportError(
                    "Google Gen AI is not available. Please install it:\n"
                    "  pip install google-generative-ai"
                )
            agent = GooglePalm(model=model, api_key=api_key)
        
        elif agent_type.lower() == "langchain-azure-openai":
            model = kwargs.get("model", "gpt-4")
            api_key = utils._get_api_key('langchain-azure-openai', kwargs.get("azure_openai_api_key"))
            deployment_name=kwargs.get("azure_model_deployment_name","your_deployment_name")
            api_base=kwargs.get("azure_endpoint", "https://your-resource-name.openai.azure.com/")
            
            try:
                from langchain.llms import AzureOpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI is not available. Please install it:\n"
                    "  pip install openai"
                )
            agent = AzureOpenAI(deployment_name=deployment_name, model=model, api_key=api_key, api_base=api_base)
        
        elif agent_type.lower() == "langchain-writer":
            model = kwargs.get("model", "palmyra-large")
            api_key = utils._get_api_key('langchain-writer', kwargs.get("writer_api_key"))
            
            try:
                from langchain.llms import Writer
            except ImportError:
                raise ImportError(
                    "Writer is not available. Please install it:\n"
                    "  pip install writerai"
                )
            agent = Writer(model=model, api_key=api_key)

        elif agent_type.lower() == "huggingface":
            try:
                from transformers import pipeline
            except ImportError:
                raise ImportError(
                    "The Hugging Face module is not available. Please install it:\n"
                    "  pip install transformers"
                )
            task = kwargs.get("task", "text-generation")
            model = kwargs.get("model", "gpt2")
            agent = pipeline(task, model=model)

        elif agent_type.lower() == "openai":
            # Create an OpenAI agent directly
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "OpenAI is not available. Please install it:\n"
                    "  pip install openai"
                )
                
            openai.api_key = utils._get_api_key('openai', kwargs.get("openai_api_key"))
            agent = openai
        elif agent_type.lower() == "deepseek":
            # Deep Seek use the OpenAI SDK.
            try:
                import openai
            except ImportError:
                raise ImportError(
                    "The OpenAI SDK is required for Deep Seek. Please install it:\n"
                    "  pip install openai"
                )

            openai.api_base = kwargs.get("api_base", "https://api.deepseek.com")
            openai.api_key = utils._get_api_key('deepseek', kwargs.get("deepseek_api_key"))
            agent = openai
        else:
            raise ValueError(f"Unsupported agent type: {agent_type}")
            
        return agent