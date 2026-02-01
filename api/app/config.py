from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # NeuralGraphDB
    neuralgraph_url: str = "http://neuralgraph:3000"

    # API
    api_title: str = "Newsletter API"
    api_version: str = "1.0.0"
    base_url: str = "https://neuralgraph.dev"
    debug: bool = False  # Set to True for development (enables query logging)

    # CORS
    cors_origins: str = ""  # Comma-separated list of allowed origins, empty = allow all (dev only)

    # Security (min 32 bytes for HS256)
    secret_key: str = "change-me-in-production-min-32-bytes"
    token_expire_days: int = 7
    admin_api_key: str = ""  # Legacy: single API key for admin access (format: nk_...)
    admin_username: str = "admin"
    admin_password: str = ""  # Set via ADMIN_PASSWORD env var

    # Email (Resend)
    resend_api_key: str = ""
    from_email: str = "newsletter@example.com"

    # Rate limiting
    rate_limit_requests: int = 10
    rate_limit_window: int = 60  # seconds

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if not self.cors_origins:
            return ["*"] if self.debug else []
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
