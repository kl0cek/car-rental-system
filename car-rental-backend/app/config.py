from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "DriveEase API"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    DATABASE_URL: str
    MONGODB_URL: str
    REDIS_URL: str

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
