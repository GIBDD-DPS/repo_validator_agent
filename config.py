import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Prizolov Repo Validator"
    debug: bool = False
    
    # Redis настройки
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    cache_ttl_seconds: int = 7 * 24 * 3600  # 7 дней
    
    # GitHub API
    github_api_timeout: int = 10
    
    class Config:
        env_file = ".env"

settings = Settings()
