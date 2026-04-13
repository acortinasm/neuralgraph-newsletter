from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neuralgraph_uri: str = "bolt://graph.coraldatalab.com:7687"
    admin_api_key: str = "change-me"
    resend_api_key: str = ""
    from_email: str = "newsletter@coraldatalab.com"
    base_url: str = "http://localhost:8000"
    cors_origins: list[str] = ["http://localhost:3000"]
    tracking_secret: str = "change-me-to-a-random-string"

    model_config = {"env_file": ".env"}


settings = Settings()
