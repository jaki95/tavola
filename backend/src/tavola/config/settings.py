from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Tavola API"
    environment: str = "local"
    api_prefix: str = "/api"
