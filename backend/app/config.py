from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    subconscious_api_key: str = ""
    fal_key: str = ""
    engine: str = "tim-gpt"
    cors_origins: list[str] = ["http://localhost:5173"]
    max_upload_mb: int = 50

    model_config = {"env_file": str(_ENV_FILE), "env_prefix": ""}


settings = Settings()
