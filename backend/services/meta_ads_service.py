# services/meta_ads_service.py
import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException

from config.config import settings
from services.ad_platform_service import AdPlatformService
from utils.helpers import handle_meta_ads_error

logger = logging.getLogger(__name__)

META_CTA_OPTIONS = ("LEARN_MORE", "SHOP_NOW", "SIGN_UP", "CONTACT_US", "BOOK_NOW")


def _truncate(value: str, limit: int) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[:limit].rstrip()


def _account_id() -> str:
    ad_account_id = settings.meta_ad_account_id or ""
    return ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"


class MockMetaAdsService(AdPlatformService):
    def __init__(self):
        self.campaign_templates = {
            "restaurant": {
                "primary_texts": [
                    "Hungry for {cuisine}? Visit {name} in {location} for fresh favorites, warm service, and easy booking today.",
                    "Make tonight delicious with {name}. Discover {cuisine} dishes made for locals in {location}.",
                    "Bring friends, bring appetite. {name} serves memorable {cuisine} meals in {location}.",
                ],
                "headlines": [
                    "{cuisine} Dining in {location}",
                    "Book {name} Today",
                    "Fresh {cuisine} Near You",
                ],
                "descriptions": [
                    "Book your table today",
                    "Fresh dishes daily",
                    "Local favorite",
                ],
                "call_to_action": "BOOK_NOW",
            },
            "retail": {
                "primary_texts": [
                    "Discover quality {product} from {name}. Shop customer favorites, seasonal picks, and easy online ordering today.",
                    "Upgrade your day with {product} from {name}. Browse fresh arrivals and limited-time offers.",
                    "Find {product} made for your style at {name}. Shop now and get fast, simple checkout.",
                ],
                "headlines": [
                    "Shop {product} Today",
                    "New {product} Arrivals",
                    "Quality {product} Deals",
                ],
                "descriptions": [
                    "Shop new arrivals",
                    "Fast checkout",
                    "Limited offers",
                ],
                "call_to_action": "SHOP_NOW",
            },
        }

    async def generate_campaign_preview(self, business_info: Dict, db=None) -> Dict:
        try:
            business_type = business_info.get("type", "").lower()
            template = self.campaign_templates.get(business_type, self.campaign_templates["retail"])
            details = {
                "name": business_info.get("name") or "Your Business",
                "cuisine": business_info.get("cuisine") or "local",
                "location": business_info.get("location") or "your area",
                "product": business_info.get("product") or "products",
            }

            primary_texts = self._format_templates(template["primary_texts"], details, 125)
            headlines = self._format_templates(template["headlines"], details, 40)
            descriptions = self._format_templates(template["descriptions"], details, 30)
            call_to_action = business_info.get("call_to_action") or template["call_to_action"]
            if call_to_action not in META_CTA_OPTIONS:
                call_to_action = "LEARN_MORE"

            return {
                "platform": "meta",
                "primary_texts": primary_texts[:3],
                "primary_text": primary_texts[0] if primary_texts else "",
                "headlines": headlines[:3],
                "descriptions": descriptions[:2],
                "description": descriptions[0] if descriptions else "",
                "keywords": [],
                "page_id": business_info.get("page_id") or settings.meta_page_id or "mock_page_12345",
                "call_to_action": call_to_action,
                "asset_url": business_info.get("asset_url") or "",
                "link_url": business_info.get("link_url") or "https://example.com",
                "daily_budget": business_info.get("daily_budget", 10),
                "location": business_info.get("location") or "Online",
                "target_audience": business_info.get("target_audience") or {},
                "estimated_metrics": self._generate_mock_metrics(),
            }
        except Exception as e:
            logger.error(f"Error generating mock Meta campaign preview: {e}")
            raise

    async def create_campaign(self, campaign_data: Dict) -> Dict:
        try:
            await asyncio.sleep(1)
            campaign_id = f"mock_meta_campaign_{random.randint(1000, 9999)}"
            return {
                "platform": "meta",
                "campaign_id": campaign_id,
                "status": "success",
                "preview_url": f"https://business.facebook.com/adsmanager/manage/campaigns?selected_campaign_ids={campaign_id}",
                "page_id": campaign_data.get("page_id") or settings.meta_page_id or "mock_page_12345",
                "call_to_action": campaign_data.get("call_to_action") or "LEARN_MORE",
                "created_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error creating mock Meta campaign: {e}")
            raise

    def _format_templates(self, templates: List[str], details: Dict, limit: int) -> List[str]:
        formatted = []
        for template in templates:
            try:
                formatted.append(_truncate(template.format(**details), limit))
            except KeyError:
                continue
        return formatted

    def _generate_mock_metrics(self) -> Dict:
        return {
            "reach": random.randint(2500, 9000),
            "impressions": random.randint(3500, 12000),
            "clicks": random.randint(80, 360),
            "engagements": random.randint(120, 700),
            "ctr": round(random.uniform(0.8, 3.2), 2),
            "cpm": round(random.uniform(4.0, 12.0), 2),
            "cost": round(random.uniform(80, 450), 2),
        }


class RealMetaAdsService(AdPlatformService):
    def __init__(self):
        self.api = None
        self._init_client()

    def _init_client(self):
        try:
            from facebook_business.api import FacebookAdsApi

            FacebookAdsApi.init(
                app_id=settings.meta_app_id,
                app_secret=settings.meta_app_secret,
                access_token=settings.meta_access_token,
            )
            self.api = FacebookAdsApi.get_default_api()
        except Exception as e:
            logger.error(f"Failed to initialize Meta Ads API client: {e}")

    async def generate_campaign_preview(self, business_info: Dict, db=None) -> Dict:
        mock_service = MockMetaAdsService()
        preview = await mock_service.generate_campaign_preview(business_info, db)

        if not self.api:
            logger.warning("Meta Ads API client not initialized; returning mock preview.")
            return preview

        try:
            await self._validate_campaign_payload({
                "campaign_name": f"Dry Run Meta Campaign {random.randint(1000, 9999)}",
            })
            return preview
        except Exception as e:
            formatted = handle_meta_ads_error(e)
            logger.error(f"Meta Ads API Dry-Run Error: {formatted}")
            raise HTTPException(status_code=400, detail=formatted)

    async def create_campaign(self, campaign_data: Dict) -> Dict:
        if not self.api:
            raise HTTPException(status_code=400, detail="Meta Ads API client not initialized. Configure Meta credentials first.")

        try:
            await self._validate_campaign_payload(campaign_data)
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: self._create_campaign_sync(campaign_data))
        except HTTPException:
            raise
        except Exception as e:
            formatted = handle_meta_ads_error(e)
            logger.error(f"Meta Ads API Creation Error: {formatted}")
            raise HTTPException(status_code=400, detail=formatted)

    async def _validate_campaign_payload(self, campaign_data: Dict) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._create_campaign_shell(campaign_data, validate_only=True))

    def _create_campaign_sync(self, campaign_data: Dict) -> Dict:
        campaign = self._create_campaign_shell(campaign_data, validate_only=False)
        campaign_id = campaign.get("id")

        from facebook_business.adobjects.adaccount import AdAccount

        account = AdAccount(_account_id())
        adset = account.create_ad_set(fields=[], params=self._adset_params(campaign_data, campaign_id))
        creative = account.create_ad_creative(fields=[], params=self._creative_params(campaign_data))
        ad = account.create_ad(fields=[], params={
            "name": campaign_data.get("ad_name") or f"Ad {int(datetime.now().timestamp())}",
            "adset_id": adset.get("id"),
            "creative": {"creative_id": creative.get("id")},
            "status": "PAUSED",
        })

        return {
            "platform": "meta",
            "campaign_id": campaign_id,
            "adset_id": adset.get("id"),
            "creative_id": creative.get("id"),
            "ad_id": ad.get("id"),
            "status": "success",
            "preview_url": f"https://business.facebook.com/adsmanager/manage/campaigns?selected_campaign_ids={campaign_id}",
            "created_at": datetime.now().isoformat(),
        }

    def _create_campaign_shell(self, campaign_data: Dict, validate_only: bool):
        from facebook_business.adobjects.adaccount import AdAccount

        params = self._campaign_params(campaign_data)
        if validate_only:
            params["execution_options"] = ["validate_only"]
        return AdAccount(_account_id()).create_campaign(fields=[], params=params)

    def _campaign_params(self, campaign_data: Dict) -> Dict:
        return {
            "name": campaign_data.get("campaign_name") or f"Meta Campaign {int(datetime.now().timestamp())}",
            "objective": campaign_data.get("objective") or "OUTCOME_TRAFFIC",
            "status": "PAUSED",
            "special_ad_categories": campaign_data.get("special_ad_categories") or [],
        }

    def _adset_params(self, campaign_data: Dict, campaign_id: str) -> Dict:
        return {
            "name": campaign_data.get("adset_name") or f"Ad Set {int(datetime.now().timestamp())}",
            "campaign_id": campaign_id,
            "daily_budget": int(float(campaign_data.get("daily_budget", 10)) * 100),
            "billing_event": "IMPRESSIONS",
            "optimization_goal": campaign_data.get("optimization_goal") or "LINK_CLICKS",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "targeting": self._targeting(campaign_data),
            "start_time": (datetime.utcnow() + timedelta(minutes=10)).isoformat(),
            "status": "PAUSED",
        }

    def _creative_params(self, campaign_data: Dict) -> Dict:
        page_id = campaign_data.get("page_id") or settings.meta_page_id
        link_url = campaign_data.get("link_url") or "https://example.com"
        primary_text = self._first(campaign_data, "primary_texts", "primary_text")
        headline = self._first(campaign_data, "headlines", "headline")
        description = self._first(campaign_data, "descriptions", "description")
        call_to_action = campaign_data.get("call_to_action") or "LEARN_MORE"

        link_data = {
            "message": _truncate(primary_text, 125),
            "link": link_url,
            "name": _truncate(headline, 40),
            "description": _truncate(description, 30),
            "call_to_action": {
                "type": call_to_action,
                "value": {"link": link_url},
            },
        }

        if campaign_data.get("image_hash"):
            link_data["image_hash"] = campaign_data["image_hash"]
        elif campaign_data.get("asset_url"):
            link_data["picture"] = campaign_data["asset_url"]

        object_story_spec = {"page_id": page_id, "link_data": link_data}
        if campaign_data.get("video_id"):
            object_story_spec = {
                "page_id": page_id,
                "video_data": {
                    "video_id": campaign_data["video_id"],
                    "message": _truncate(primary_text, 125),
                    "title": _truncate(headline, 40),
                    "call_to_action": {
                        "type": call_to_action,
                        "value": {"link": link_url},
                    },
                },
            }

        return {
            "name": campaign_data.get("creative_name") or f"Creative {int(datetime.now().timestamp())}",
            "object_story_spec": object_story_spec,
        }

    def _targeting(self, campaign_data: Dict) -> Dict:
        target_audience = campaign_data.get("target_audience") or {}
        countries = target_audience.get("countries") or ["US"]
        targeting = {
            "geo_locations": {"countries": countries},
            "age_min": target_audience.get("age_min", 18),
            "age_max": target_audience.get("age_max", 65),
        }
        if target_audience.get("genders"):
            targeting["genders"] = target_audience["genders"]
        if target_audience.get("interests"):
            targeting["interests"] = target_audience["interests"]
        return targeting

    def _first(self, campaign_data: Dict, list_key: str, value_key: str) -> str:
        values = campaign_data.get(list_key) or []
        if values:
            return values[0]
        return campaign_data.get(value_key) or ""


def is_meta_ads_configured() -> bool:
    return bool(settings.is_meta_ads_configured)


def get_meta_ads_service():
    if is_meta_ads_configured():
        return RealMetaAdsService()
    return MockMetaAdsService()
