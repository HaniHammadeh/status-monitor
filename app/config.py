from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Central app configuration. Values are read from environment variables
    first, falling back to .env, falling back to the defaults below.
    In docker-compose / Kubernetes, these are overridden by env vars.
    """

    database_url: str = "postgresql://statususer:statuspass@localhost:5432/statusdb"
    redis_url: str = "redis://localhost:6379/0"
    app_name: str = "Status Monitor"
    health_check_interval_seconds: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
