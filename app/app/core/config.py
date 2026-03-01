from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://delegato:delegato@postgres:5432/delegato"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-random-secret"
    JWT_REFRESH_SECRET_KEY: str = "change-me-to-another-random-secret"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Email (Unisender Go)
    UNISENDER_API_KEY: str = ""
    UNISENDER_FROM_EMAIL: str = "noreply@delegato.ru"
    UNISENDER_FROM_NAME: str = "Delegato"
    UNISENDER_BASE_URL: str = "https://goapi.unisender.ru/ru/transactional/api/v1"

    # Payment Provider
    PAYMENT_PROVIDER: str = "tbank"
    PAYMENT_SECRET_KEY: str = ""
    PAYMENT_TERMINAL_KEY: str = ""
    PAYMENT_WEBHOOK_IPS: str = ""

    # Claude API
    CLAUDE_API_KEY: str = ""

    # Sentry
    SENTRY_DSN: str = ""

    # Admin
    ADMIN_WHITELIST_IPS: str = "127.0.0.1"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Infrastructure (Terraform + Ansible)
    TIMEWEB_API_TOKEN: str = ""
    TIMEWEB_REGION: str = "nl-1"
    TIMEWEB_SSH_KEY_ID: str = ""
    TERRAFORM_STATE_BUCKET: str = ""
    TERRAFORM_STATE_ENDPOINT: str = "https://s3.twcstorage.ru"
    TERRAFORM_STATE_ACCESS_KEY: str = ""
    TERRAFORM_STATE_SECRET_KEY: str = ""
    SSH_PRIVATE_KEY_PATH: str = "~/.ssh/delegata_rsa"
    INFRASTRUCTURE_DIR: str = "infrastructure"
    OPENCLAW_DOCKER_IMAGE: str = "ghcr.io/openclaw/openclaw:latest"

    # App
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def admin_whitelist_ips_list(self) -> list[str]:
        return [ip.strip() for ip in self.ADMIN_WHITELIST_IPS.split(",") if ip.strip()]

    @property
    def payment_webhook_ips_list(self) -> list[str]:
        if not self.PAYMENT_WEBHOOK_IPS:
            return []
        return [ip.strip() for ip in self.PAYMENT_WEBHOOK_IPS.split(",") if ip.strip()]


settings = Settings()
