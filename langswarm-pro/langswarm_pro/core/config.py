from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "LangSwarm Pro"
    
    # Auth
    JWT_SECRET_KEY: str = "changeme"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Governance
    GOVERNANCE_ENABLED: bool = True
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
