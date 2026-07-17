from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum
from functools import cached_property

class AdvertisingPlatform(str, Enum):
    NONE = "none"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        use_enum_values=True,
        extra="ignore"
    )

    # Basic API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = True
    
    # Advertising Platform Selection
    advertising_platform: AdvertisingPlatform = AdvertisingPlatform.NONE
    
    # Optional Google Ads Configuration
    google_ads_client_id: Optional[str] = None
    google_ads_client_secret: Optional[str] = None
    google_ads_developer_token: Optional[str] = None
    google_ads_login_customer_id: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # CORS Configuration
    allowed_origins: list = ["http://localhost:3000"]
    
    # AI Model Configuration
    model_provider: str = "gemini"
    model_name: str = "gemini-1.5-flash"
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    
    @cached_property
    def is_google_ads_enabled(self) -> bool:
        """Check if basic Google Ads configuration is available"""
        return all([
            self.advertising_platform == AdvertisingPlatform.GOOGLE_ADS,
            self.google_ads_client_id,
            self.google_ads_client_secret
        ])
    
    @field_validator('advertising_platform', mode='before')
    @classmethod
    def validate_advertising_platform(cls, v):
        if isinstance(v, str):
            return AdvertisingPlatform(v.lower())
        return v
    
    def validate_startup(self):
        """Fail fast on misconfigurations if Google Ads platform is selected."""
        if self.advertising_platform == AdvertisingPlatform.GOOGLE_ADS:
            missing = []
            if not self.google_ads_client_id:
                missing.append("GOOGLE_ADS_CLIENT_ID")
            if not self.google_ads_client_secret:
                missing.append("GOOGLE_ADS_CLIENT_SECRET")
            if missing:
                raise ValueError(
                    f"Configuration error: {', '.join(missing)} must be set when advertising_platform is 'google_ads'."
                )
    
    def get_google_ads_config(self) -> dict:
        """
        Get Google Ads configuration if available.
        Returns empty dict if not configured.
        """
        if not self.is_google_ads_enabled:
            return {}
            
        return {
            'client_id': self.google_ads_client_id,
            'client_secret': self.google_ads_client_secret,
        }

settings = Settings()
settings.validate_startup()