from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DriveEase API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # PostgreSQL
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # MongoDB
    MONGODB_URL: str

    # Redis
    REDIS_URL: str

    model_config = {"env_file": (".env", "../.env"), "case_sensitive": True}


settings = Settings()
