"""Application settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "MultiscaleNano"
    debug: bool = True
    database_url: str = "postgresql+asyncpg://multiscale:multiscale@localhost:5432/multiscale"
    redis_url: str = "redis://localhost:6379/0"
    artifact_root: str = "./artifacts"
    gromacs_image: str = "multiscale/gromacs:latest"
    cors_origins: list[str] = ["http://localhost:3000"]

    model_config = {"env_prefix": "MN_"}


settings = Settings()
