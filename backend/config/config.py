from pydantic import BaseSettings, validator
from typing import Optional
from enum import Enum
from functools import cached_property

class AdvertisingPlatform(str, Enum):
    NONE = "none"
    GOOGLE_ADS = "google_ads"
    FACEBOOK_ADS = "facebook_ads"

class Settings(BaseSettings):
    # Basic API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug_mode: bool = True
    
    # Advertising Platform Selection
    advertising_platform: AdvertisingPlatform = AdvertisingPlatform.NONE
    
    # Optional Google Ads Configuration
    google_ads_client_id: Optional[str] = None
    google_ads_client_secret: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # CORS Configuration
    allowed_origins: list = ["http://localhost:3000"]
    
    # AI Model Configuration
    model_name: str = "deepseek-ai/deepseek-coder-6.7b-base"
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
    
    @validator('advertising_platform', pre=True)
    def validate_advertising_platform(cls, v):
        if isinstance(v, str):
            return AdvertisingPlatform(v.lower())
        return v
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        use_enum_values = True

settings = Settings()