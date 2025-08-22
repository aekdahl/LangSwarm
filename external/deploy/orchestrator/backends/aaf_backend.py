"""
AAF Backend Manager for LangSwarm-powered instances
"""
import json
import subprocess
import logging
import asyncio
from typing import Dict, Any, List, Optional
import aiohttp
from datetime import datetime

from .base_backend import BackendManager, BackendCapabilities

logger = logging.getLogger(__name__)


class AAFBackendManager(BackendManager):
    """Manager for AAF (LangSwarm-powered) backends"""
    
    def __init__(self, project_id: str, region: str = "europe-west1"):
        super().__init__(project_id, region)
        self.backend_type = "aaf"
        self.image_base = "europe-west1-docker.pkg.dev/enkl-saas/aaf-images/aaf-backend"
        self.capabilities = BackendCapabilities(
            create=True,            # Can create new instances
            adopt=True,             # Can adopt existing instances
            delete=True,            # Can delete instances
            update_prompts=True,    # Can update prompts via config API
            remove_from_admin=False # Delete removes completely
        )
        
        # In-memory storage for instances
        # In production, this should be a database
        self.instances = {}
    
    async def deploy_instance(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a new AAF instance"""
        logger.info(f"Deploying new AAF instance: {config.get('instance_name', 'unnamed')}")
        
        # Extract configuration
        instance_name = config.get("instance_name") or f"aaf-instance-{int(datetime.utcnow().timestamp())}"
        image_tag = config.get("image_tag", "latest")
        memory = config.get("memory", "2Gi")
        cpu = config.get("cpu", "1")
        max_instances = config.get("max_instances", 10)
        
        # Environment variables
        env_vars = self._build_env_vars(config)
        
        try:
            # Deploy to Cloud Run
            image_url = f"{self.image_base}:{image_tag}"
            
            cmd = [
                "gcloud", "run", "deploy", instance_name,
                "--image", image_url,
                "--project", self.project_id,
                "--region", self.region,
                "--memory", memory,
                "--cpu", cpu,
                "--max-instances", str(max_instances),
                "--allow-unauthenticated",
                "--format", "json"
            ]
            
            # Add environment variables
            if env_vars:
                env_string = ",".join([f"{k}={v}" for k, v in env_vars.items()])
                cmd.extend(["--set-env-vars", env_string])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Deployment failed: {result.stderr}")
            
            deployment_result = json.loads(result.stdout)
            service_url = deployment_result.get("status", {}).get("url")
            
            # Wait for service to be ready and validate health
            await self._wait_for_service_ready(service_url)
            
            # Create instance record
            instance_record = self.create_instance_record(instance_name, {
                "deployed_at": datetime.utcnow().isoformat(),
                "service_url": service_url,
                "image": image_url,
                "configuration": config,
                "capabilities": self.capabilities.to_dict()
            })
            
            # Store instance
            self.instances[instance_name] = instance_record
            
            logger.info(f"Successfully deployed AAF instance: {instance_name}")
            return instance_record
            
        except Exception as e:
            logger.error(f"Failed to deploy AAF instance: {e}")
            raise
    
    async def adopt_instance(self, service_name: str, **kwargs) -> Dict[str, Any]:
        """Adopt an existing AAF instance"""
        logger.info(f"Attempting to adopt AAF instance: {service_name}")
        
        # Get service URL
        service_url = await self.get_service_url(service_name)
        if not service_url:
            raise ValueError(f"Service {service_name} not found in project {self.project_id}")
        
        # Validate service health and compatibility
        health_check = await self.validate_service_health(service_url)
        if not health_check["valid"]:
            raise ValueError(f"Service validation failed: {health_check['error']}")
        
        health_data = health_check["health_data"]
        
        # Verify it's an AAF backend
        if health_data.get("backend_type") != "aaf" and "langswarm" not in health_data.get("service", "").lower():
            raise ValueError(
                f"Service is not an AAF backend (found: {health_data.get('backend_type', 'unknown')})"
            )
        
        # Get or generate management API secret
        management_secret = await self._get_or_generate_management_secret(service_name)
        
        # Create instance record
        instance_record = self.create_instance_record(service_name, {
            "adopted_at": datetime.utcnow().isoformat(),
            "service_url": service_url,
            "management_api_secret": management_secret,
            "capabilities": self.capabilities.to_dict(),
            "health_data": health_data
        })
        
        # Store instance
        self.instances[service_name] = instance_record
        
        logger.info(f"Successfully adopted AAF instance: {service_name}")
        return instance_record
    
    async def update_prompts(self, instance_id: str, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Update AAF instance prompts via LangSwarm config API"""
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        service_url = instance["service_url"]
        management_secret = instance.get("management_api_secret")
        
        # Convert prompts to LangSwarm config format
        langswarm_config = self._prompts_to_langswarm_config(prompts)
        
        try:
            headers = {"Content-Type": "application/json"}
            if management_secret:
                headers["Authorization"] = f"Bearer {management_secret}"
            
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{service_url}/api/config/update",
                    json=langswarm_config,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Config update failed: HTTP {response.status} - {error_text}")
                    
                    result = await response.json()
                    
                    return {
                        "success": True,
                        "method": "langswarm_config",
                        "updated_prompts": list(prompts.keys()),
                        "restart_required": False,
                        "timestamp": datetime.utcnow().isoformat(),
                        "config_result": result
                    }
                    
        except Exception as e:
            logger.error(f"Failed to update AAF prompts: {e}")
            return {
                "success": False,
                "method": "langswarm_config",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_prompts(self, instance_id: str) -> Dict[str, Any]:
        """Get current AAF instance configuration"""
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        service_url = instance["service_url"]
        management_secret = instance.get("management_api_secret")
        
        try:
            headers = {}
            if management_secret:
                headers["Authorization"] = f"Bearer {management_secret}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{service_url}/api/config",
                    headers=headers,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get config: HTTP {response.status}")
                    
                    config = await response.json()
                    
                    # Extract prompts from LangSwarm config
                    return self._langswarm_config_to_prompts(config)
                    
        except Exception as e:
            logger.error(f"Failed to get AAF prompts for {instance_id}: {e}")
            raise
    
    async def get_prompt_schema(self, instance_id: str) -> Dict[str, Any]:
        """Get AAF prompt schema (standard LangSwarm fields)"""
        # AAF instances have a standard prompt schema
        return {
            "fields": [
                {
                    "name": "system_prompt",
                    "label": "System Prompt",
                    "type": "textarea",
                    "required": True,
                    "description": "The main system prompt for the AI agent"
                },
                {
                    "name": "model",
                    "label": "AI Model",
                    "type": "select",
                    "options": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
                    "default": "gpt-4o",
                    "description": "The AI model to use"
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "range",
                    "min": 0,
                    "max": 1,
                    "step": 0.1,
                    "default": 0.7,
                    "description": "Controls randomness in responses"
                },
                {
                    "name": "welcome_message",
                    "label": "Welcome Message",
                    "type": "text",
                    "description": "Initial message shown to users"
                }
            ]
        }
    
    async def list_instances(self) -> List[Dict[str, Any]]:
        """List all AAF instances"""
        return list(self.instances.values())
    
    async def delete_instance(self, instance_id: str) -> bool:
        """Delete an AAF instance from Cloud Run"""
        try:
            result = subprocess.run([
                "gcloud", "run", "services", "delete", instance_id,
                "--project", self.project_id,
                "--region", self.region,
                "--quiet"
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to delete service: {result.stderr}")
                return False
            
            # Remove from tracking
            if instance_id in self.instances:
                del self.instances[instance_id]
            
            logger.info(f"Successfully deleted AAF instance: {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete AAF instance {instance_id}: {e}")
            return False
    
    async def get_instance_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed AAF instance information"""
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        
        # Enhance with current health status
        try:
            health_check = await self.validate_service_health(instance["service_url"])
            instance = instance.copy()
            instance["current_health"] = health_check
        except Exception as e:
            logger.warning(f"Failed to get current health for {instance_id}: {e}")
        
        return instance
    
    def _build_env_vars(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Build environment variables for AAF deployment"""
        env_vars = {}
        
        # Required environment variables
        if "openai_api_key" in config:
            env_vars["OPENAI_API_KEY"] = config["openai_api_key"]
        
        if "bigquery_dataset_id" in config:
            env_vars["BIGQUERY_DATASET_ID"] = config["bigquery_dataset_id"]
        
        if "crawl4ai_base_url" in config:
            env_vars["CRAWL4AI_BASE_URL"] = config["crawl4ai_base_url"]
        
        if "management_api_secret" in config:
            env_vars["MANAGEMENT_API_SECRET"] = config["management_api_secret"]
        
        # Optional environment variables
        optional_vars = [
            "cors_origins", "cors_allow_methods", "cors_allow_headers",
            "huggingface_api_key", "anthropic_api_key"
        ]
        
        for var in optional_vars:
            if var in config:
                env_vars[var.upper()] = str(config[var])
        
        return env_vars
    
    async def _wait_for_service_ready(self, service_url: str, max_attempts: int = 30) -> bool:
        """Wait for the deployed service to be ready"""
        for attempt in range(max_attempts):
            try:
                health_check = await self.validate_service_health(service_url)
                if health_check["valid"]:
                    return True
            except Exception:
                pass
            
            if attempt < max_attempts - 1:
                await asyncio.sleep(10)
        
        raise Exception("Service did not become ready within timeout")
    
    async def _get_or_generate_management_secret(self, service_name: str) -> str:
        """Get existing management secret or generate a new one"""
        try:
            # Try to get existing secret from service environment
            result = subprocess.run([
                "gcloud", "run", "services", "describe", service_name,
                "--project", self.project_id,
                "--region", self.region,
                "--format", "json"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                service_data = json.loads(result.stdout)
                env_vars = service_data.get("spec", {}).get("template", {}).get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("env", [])
                
                for env_var in env_vars:
                    if env_var.get("name") == "MANAGEMENT_API_SECRET":
                        return env_var.get("value", "")
            
            # Generate new secret if not found
            import secrets
            new_secret = secrets.token_urlsafe(32)
            
            # Update service with new secret
            subprocess.run([
                "gcloud", "run", "services", "update", service_name,
                "--project", self.project_id,
                "--region", self.region,
                "--update-env-vars", f"MANAGEMENT_API_SECRET={new_secret}"
            ], capture_output=True, text=True)
            
            return new_secret
            
        except Exception as e:
            logger.warning(f"Failed to get/generate management secret: {e}")
            return ""
    
    def _prompts_to_langswarm_config(self, prompts: Dict[str, str]) -> Dict[str, Any]:
        """Convert prompt dictionary to LangSwarm configuration format"""
        # Basic LangSwarm config structure
        config = {
            "agents": [
                {
                    "id": "aaf_chatbot",
                    "system_prompt": prompts.get("system_prompt", "You are a helpful assistant."),
                    "model": prompts.get("model", "gpt-4o"),
                    "temperature": float(prompts.get("temperature", 0.7))
                }
            ]
        }
        
        # Add other configuration if present
        if "welcome_message" in prompts:
            config["welcome_message"] = prompts["welcome_message"]
        
        return config
    
    def _langswarm_config_to_prompts(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract prompts from LangSwarm configuration"""
        prompts = {}
        
        # Extract from agents
        agents = config.get("agents", [])
        if agents:
            agent = agents[0]  # Use first agent
            prompts["system_prompt"] = agent.get("system_prompt", "")
            prompts["model"] = agent.get("model", "gpt-4o")
            prompts["temperature"] = str(agent.get("temperature", 0.7))
        
        # Extract other fields
        if "welcome_message" in config:
            prompts["welcome_message"] = config["welcome_message"]
        
        return prompts
