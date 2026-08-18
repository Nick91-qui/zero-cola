from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "COLA-ZERO"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://colazero:colazero@postgres:5432/colazero"
    secret_key: str = "dev-secret-key-change-in-production"
    omr_storage_backend: str = "local"
    omr_storage_local_dir: str = "uploads/scans"
    omr_storage_minio_endpoint: str | None = None
    omr_storage_minio_access_key: str | None = None
    omr_storage_minio_secret_key: str | None = None
    omr_storage_minio_bucket: str = "cola-zero-omr"
    omr_storage_minio_secure: bool = False
    omr_storage_minio_public_base_url: str | None = None


settings = Settings()
