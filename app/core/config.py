from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./poetry.db", alias="DATABASE_URL")
    cors_origins_raw: str = Field(default="*", alias="CORS_ORIGINS")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    backend_public_url: str = Field(default="http://localhost:8000", alias="BACKEND_PUBLIC_URL")
    webhook_secret: str = Field(default="super-secret", alias="WEBHOOK_SECRET")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="admin123", alias="ADMIN_PASSWORD")
    
    # Reminder settings
    reminder_enabled: bool = Field(default=True, alias="REMINDER_ENABLED")
    reminder_hour: int = Field(default=12, alias="REMINDER_HOUR")
    reminder_inactivity_days: int = Field(default=3, alias="REMINDER_INACTIVITY_DAYS")
    timezone: str = Field(default="UTC", alias="TIMEZONE")

    @property
    def cors_origins(self) -> list[str]:
        raw = self.cors_origins_raw.strip()
        if raw == "*":
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]


settings = Settings()
