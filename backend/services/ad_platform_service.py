from abc import ABC, abstractmethod
from typing import Dict, List


SUPPORTED_AD_PLATFORMS = ("google", "meta")
SUPPORTED_PLATFORM_SELECTIONS = (*SUPPORTED_AD_PLATFORMS, "both")


class AdPlatformService(ABC):
    @abstractmethod
    async def generate_campaign_preview(self, business_info: dict, db=None) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def create_campaign(self, campaign_data: dict) -> dict:
        raise NotImplementedError


def expand_platform_selection(platform: str) -> List[str]:
    normalized = (platform or "google").lower()
    if normalized == "both":
        return ["google", "meta"]
    if normalized in SUPPORTED_AD_PLATFORMS:
        return [normalized]
    raise ValueError(f"Unsupported advertising platform: {platform}")


def get_ad_platform_service(platform: str) -> AdPlatformService:
    normalized = (platform or "google").lower()
    if normalized == "google":
        from services.google_ads_service import get_google_ads_service

        return get_google_ads_service()
    if normalized == "meta":
        from services.meta_ads_service import get_meta_ads_service

        return get_meta_ads_service()
    raise ValueError(f"Unsupported advertising platform: {platform}")
