from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    API_KEY: str

    # Redis Settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_CACHE_EXPIRY: int

    # MongoDB Settings
    MONGODB_URL: str = "mongodb://mongodb:27017"
    MONGODB_DB: str = "bittensor_api"

    # Bittensor Settings
    BITTENSOR_NETWORK: str
    WALLET_NAME: str
    WALLET_HOTKEY: str
    WALLET_PATH: str
    WALLET_COLDKEY_PASSWORD: str

    DEFAULT_HOTKEY: str
    DEFAULT_NETUID: int

    # External API Keys
    DATURA_API_KEY: str
    CHUTES_API_KEY: str

    # Celery Settings
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"

settings = Settings() 