from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    subconscious_api_key: str = ""
    engine: str = "tim-gpt"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_prefix": ""}


settings = Settings()
