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

    # Cache
    USER_CACHE_TTL_SECONDS: int = 300

    # Auth
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    RESET_PASSWORD_TOKEN_EXPIRE_HOURS: int = 1

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@driveease.com"
    SMTP_TLS: bool = True

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = {
        "env_file": (".env", "../.env"),
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
