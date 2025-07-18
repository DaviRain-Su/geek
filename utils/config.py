import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    mongodb_db: str = os.getenv("MONGODB_DB", "wechat_crawler")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Crawler settings
    crawl_delay: int = int(os.getenv("CRAWL_DELAY", "5"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    timeout: int = int(os.getenv("TIMEOUT", "30"))
    
    # Proxy settings
    use_proxy: bool = os.getenv("USE_PROXY", "false").lower() == "true"
    proxy_list_file: str = os.getenv("PROXY_LIST_FILE", "proxies.txt")
    
    # Browser settings
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    viewport_width: int = 375  # Mobile viewport
    viewport_height: int = 812
    user_agent: Optional[str] = None  # Will use default mobile UA if None
    
    class Config:
        env_file = ".env"


settings = Settings()