from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./lifeos.db"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    model_config = SettingsConfigDict(env_file=Path(__file__).with_name(".env"), extra="ignore")
