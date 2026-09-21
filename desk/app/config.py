from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = Path("./data")
    database_path: Path = Path("./data/desk.db")
    public_base_url: str = "http://localhost:8000"
    alert_score_threshold: float = 70.0
    alert_webhook_url: str = ""
    alert_email: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "docket-desk@localhost"
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    # Stripe (all optional — leave empty until create_stripe_catalog.py is run)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_founding: str = ""
    stripe_price_professional: str = ""
    stripe_price_enterprise: str = ""
    stripe_founding_coupon_id: str = ""

    # Owner/admin — comma-separated emails; defaults include Anna's addresses
    admin_emails: str = "anna@annabuildsai.com,hello@aestheticabodes.ca"
    admin_token: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
