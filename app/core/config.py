from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl
from typing import List
import secrets


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: str = secrets.token_urlsafe(32)
    access_token_expire_minutes: int = 60 * 24
    algorithm: str = "HS256"

    # Database
    postgres_server: str = "localhost"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "learning"
    database_url: str | None = None

    # CORS
    cors_allow_origins: List[AnyHttpUrl] = []

    # Storage/Payments (stubs)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_s3_bucket: str | None = None

    stripe_api_key: str | None = None

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}/{self.postgres_db}"
        )


settings = Settings()
