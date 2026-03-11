from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = Field(default="GigShield API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    database_url: str = Field(
        default="",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(default="", alias="SECRET_KEY")
    admin_api_key: str = Field(default="", alias="ADMIN_API_KEY")
    access_token_ttl_minutes: int = Field(default=720, alias="ACCESS_TOKEN_TTL_MINUTES")
    otp_ttl_minutes: int = Field(default=10, alias="OTP_TTL_MINUTES")
    use_mock_sms: bool = Field(default=True, alias="USE_MOCK_SMS")
    use_mock_weather: bool = Field(default=True, alias="USE_MOCK_WEATHER")
    use_mock_payouts: bool = Field(default=True, alias="USE_MOCK_PAYOUTS")
    openweathermap_api_key: str = Field(default="", alias="OPENWEATHERMAP_API_KEY")
    twilio_account_sid: str = Field(default="", alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", alias="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", alias="TWILIO_PHONE_NUMBER")
    razorpay_key_id: str = Field(default="", alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: str = Field(default="", alias="RAZORPAY_KEY_SECRET")
    mock_weather_events: str = Field(default="heavy_rain|chennai_zone_4|3", alias="MOCK_WEATHER_EVENTS")
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOWED_ORIGINS",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def split_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
