from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")

    # Database
    database_url: str = Field(default="sqlite+aiosqlite:///./kbju.db", alias="DATABASE_URL")

    # Defaults
    default_tz: str = Field(default="Europe/Moscow", alias="DEFAULT_TZ")

    # Admin
    admin_dashboard_token: str | None = Field(default=None, alias="ADMIN_DASHBOARD_TOKEN")

    # Providers: Edamam / FDC
    edamam_app_id: str | None = Field(default=None, alias="EDAMAM_APP_ID")
    edamam_app_key: str | None = Field(default=None, alias="EDAMAM_APP_KEY")
    fdc_api_key: str | None = Field(default=None, alias="FDC_API_KEY")

    # Translate
    use_gemini_translate: bool = Field(default=False, alias="USE_GEMINI_TRANSLATE")
    use_ru_en_dictionary: bool = Field(default=False, alias="USE_RU_EN_DICTIONARY")
    only_en_for_providers: bool = Field(default=False, alias="ONLY_EN_FOR_PROVIDERS")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str | None = Field(default=None, alias="GEMINI_MODEL")

    # --- Aliases / tolerated extras from your .env ---
    # YooKassa (мы их пока не используем в коде, но разрешим чтение)
    yookassa_shop_id: str | None = Field(default=None, alias="YOOKASSA_SHOP_ID")
    yookassa_secret_key: str | None = Field(default=None, alias="YOOKASSA_SECRET_KEY")

    # Админские ID — допустим как строку (разделённую запятыми)
    admin_tg_ids: str | None = Field(default=None, alias="ADMIN_TG_IDS")

    # Доп. совместимость: если в .env указан старый ключ USE_GEMINI_TRANSLATION
    use_gemini_translation: bool | None = Field(default=None, alias="USE_GEMINI_TRANSLATION")

    # Неиспользуемый сейчас флаг — просто примем его
    disable_food_cache: bool | None = Field(default=None, alias="DISABLE_FOOD_CACHE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",  # игнорировать прочие неизвестные ключи вместо ошибки
        validate_default=False,
    )

    def __init__(self, **data):
        super().__init__(**data)
        # если указали старый USE_GEMINI_TRANSLATION=true — поднимем основной флаг
        if self.use_gemini_translation and not self.use_gemini_translate:
            object.__setattr__(self, "use_gemini_translate", True)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()