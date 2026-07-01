from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "COLA-ZERO"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql://colazero:colazero@postgres:5432/colazero"
    secret_key: str = "dev-secret-key-change-in-production"


settings = Settings()
