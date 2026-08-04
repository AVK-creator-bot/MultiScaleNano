"""Application configuration."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    use_redis_queue: bool = False
    api_url: str = "http://127.0.0.1:8000"
    artifact_dir: str = "data/artifacts"
    gromacs_container: str = "multiscale-gromacs"
    cors_origins: str = "*"

    model_config = {"env_prefix": "MULTISCALE_"}

    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

# Keep artifact dir in sync with core paths module
os.environ.setdefault("MULTISCALE_ARTIFACT_DIR", settings.artifact_dir)
