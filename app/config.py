from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    FAST_MODEL: str = "openai/gpt-4o-mini"
    DEEP_MODEL: str = "openai/gpt-4o"

    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    LOG_LEVEL: str = "INFO"

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 30


    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


settings = Settings()
