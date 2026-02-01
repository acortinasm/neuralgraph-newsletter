from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # NeuralGraphDB
    neuralgraph_url: str = "http://neuralgraph:3000"
    
    # API
    api_title: str = "Newsletter API"
    api_version: str = "1.0.0"
    base_url: str = "https://neuralgraph.dev"   
    # Security
    secret_key: str = "change-me-in-production"
    token_expire_days: int = 7
    
    # Email (configure later)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "newsletter@example.com"
    
    class Config:
        env_file = ".env"


settings = Settings()
