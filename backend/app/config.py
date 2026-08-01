from pathlib import Path

from pydantic_settings import BaseSettings

# Walk up from this file's directory to find the .env
_here = Path(__file__).resolve().parent
_env_file = _here.parent.parent / ".env"  # project root


class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str = ""

    model_config = {"env_file": str(_env_file)}


settings = Settings()
