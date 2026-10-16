from pathlib import Path

from pydantic_settings import BaseSettings

# Walk up from this file's directory to find the .env
_here = Path(__file__).resolve().parent
_env_file = _here.parent.parent / ".env"  # project root


class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str = ""
    # Comma-separated list of allowed CORS origins (e.g. the frontend's Render URL in production)
    allowed_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    # When set, part images go to this S3 bucket (credentials from the AWS credentials file).
    aws_s3_bucket: str = ""
    aws_region: str = "ap-south-1"
    aws_s3_prefix: str = "costsheet"

    model_config = {"env_file": str(_env_file)}

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
