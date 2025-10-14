from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field("sqlite+aiosqlite:///./kbju.db", alias="DATABASE_URL")

    default_tz: str = Field("Europe/Moscow", alias="DEFAULT_TZ")

    yookassa_shop_id: str | None = Field(None, alias="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str | None = Field(None, alias="YOOKASSA_SECRET_KEY")

    admin_dashboard_token: str = Field("change_me", alias="ADMIN_DASHBOARD_TOKEN")

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

settings = Settings()