from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    # URL du plugin en amont
    upstream_base_url: str  # obligatoire
    upstream_players_path: str = "/moss/players"  # celui-là peut rester par défaut

    # Cache local (TTL)
    cache_ttl_seconds: int = 20

    # Réseau
    http_timeout_seconds: int = 10

    # Garde-fou sur /top ?limit=
    max_limit: int = 200

    # Garde-fou sur /best (nombre max de stats retournées)
    max_best_results: int = 5000

    model_config = SettingsConfigDict(
        env_prefix="PSP_",
        env_file=".env",
        extra="ignore",
    )
