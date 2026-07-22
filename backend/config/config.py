import secrets as _secrets
import logging as _logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file into os.environ
load_dotenv()

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum

_logger = _logging.getLogger(__name__)

# Sentinel used to detect auto-generated JWT keys at startup
_AUTO_GENERATED_JWT_KEY = _secrets.token_hex(32)

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
    
    # Security
    jwt_secret_key: str = _AUTO_GENERATED_JWT_KEY
    
    # URL Configuration (for OAuth redirects & CORS)
    backend_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"
    
    # Legacy global advertising platform setting. Campaign requests now choose
    # their own platform, so this is retained only to avoid breaking old envs.
    advertising_platform: AdvertisingPlatform = AdvertisingPlatform.NONE
    
    # Optional Google Ads Configuration
    google_ads_client_id: Optional[str] = None
    google_ads_client_secret: Optional[str] = None
    google_ads_developer_token: Optional[str] = None
    google_ads_login_customer_id: Optional[str] = None
    google_ads_refresh_token: Optional[str] = None

    # Optional Meta Ads Configuration
    meta_app_id: Optional[str] = None
    meta_app_secret: Optional[str] = None
    meta_access_token: Optional[str] = None
    meta_ad_account_id: Optional[str] = None
    meta_page_id: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # CORS Configuration
    allowed_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # AI Model Configuration
    model_provider: str = "gemini"
    model_name: str = "gemini-3.5-flash"
    api_key: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    lm_studio_base_url: str = "http://localhost:1234/v1"
    
    @property
    def is_google_ads_enabled(self) -> bool:
        """Check if enough Google Ads configuration is available for OAuth."""
        return all([
            self.google_ads_client_id,
            self.google_ads_client_secret
        ])

    @property
    def is_google_ads_configured(self) -> bool:
        """Check if enough Google Ads configuration is available for real API calls."""
        return all([
            self.google_ads_client_id,
            self.google_ads_client_secret,
            self.google_ads_developer_token,
            self.google_ads_login_customer_id
        ])

    @property
    def is_meta_ads_configured(self) -> bool:
        """Check if enough Meta Ads configuration is available for real API calls."""
        return all([
            self.meta_app_id,
            self.meta_app_secret,
            self.meta_access_token,
            self.meta_ad_account_id,
            self.meta_page_id
        ])
    
    @field_validator('advertising_platform', mode='before')
    @classmethod
    def validate_advertising_platform(cls, v):
        if isinstance(v, str):
            return AdvertisingPlatform(v.lower())
        return v
    
    def validate_startup(self):
        """Fail fast on misconfigurations."""
        # JWT secret: must be explicitly set in non-debug environments
        if self.jwt_secret_key == _AUTO_GENERATED_JWT_KEY:
            if not self.debug_mode:
                raise ValueError(
                    "Configuration error: JWT_SECRET_KEY must be set explicitly "
                    "when DEBUG_MODE is false. Generate one with: "
                    "python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            _logger.warning(
                "JWT_SECRET_KEY is auto-generated. This is fine for local dev "
                "but must be set explicitly in production."
            )

        # Ad platform credentials are validated independently at service
        # selection time. Missing Google credentials should not prevent Meta
        # campaigns from running, and vice versa.
    
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