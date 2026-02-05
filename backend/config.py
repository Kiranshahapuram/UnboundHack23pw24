"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:password@localhost:3306/workflow_builder"
    unbound_api_key: str = ""
    unbound_base_url: str = "https://api.getunbound.ai/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
