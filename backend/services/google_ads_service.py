# services/google_ads_service.py
import os
import json
import random
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import HTTPException
from config.config import settings
from services.ad_platform_service import AdPlatformService
from utils.helpers import handle_google_ads_error

logger = logging.getLogger(__name__)

TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "google_ads_tokens.json")

def get_stored_refresh_token() -> Optional[str]:
    # Check settings / env
    if settings.google_ads_client_id and hasattr(settings, "google_ads_refresh_token") and settings.google_ads_refresh_token:
        return settings.google_ads_refresh_token
    # Read from local JSON
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)
                return data.get("refresh_token")
        except Exception as e:
            logger.error(f"Error reading google_ads_tokens.json: {e}")
    return None

def save_stored_refresh_token(refresh_token: str):
    try:
        with open(TOKEN_FILE, "w") as f:
            json.dump({"refresh_token": refresh_token}, f)
    except Exception as e:
        logger.error(f"Error writing google_ads_tokens.json: {e}")

class MockGoogleAdsService(AdPlatformService):
    def __init__(self):
        self.campaign_templates = {
            "restaurant": {
                "headlines": [
                    "Best {cuisine} Restaurant in {location}",
                    "Authentic {cuisine} Dining Experience",
                    "{cuisine} Restaurant - Book Now",
                    "Delicious {cuisine} Food Near You",
                    "Top-Rated {cuisine} Restaurant"
                ],
                "descriptions": [
                    "Enjoy authentic {cuisine} dishes in a wonderful atmosphere. Book your table today!",
                    "Fresh ingredients, traditional recipes. Visit us for the best {cuisine} experience.",
                    "Family-owned {cuisine} restaurant. Special deals available!"
                ],
                "keywords": [
                    "{cuisine} restaurant",
                    "best {cuisine} food",
                    "{cuisine} dining",
                    "{location} {cuisine} restaurant",
                    "authentic {cuisine}",
                    "{cuisine} near me"
                ]
            },
            "retail": {
                "headlines": [
                    "Quality {product} Store",
                    "Shop {product} Online",
                    "Best {product} Deals",
                    "{product} Sale - Up to 50% Off",
                    "Premium {product} Collection"
                ],
                "descriptions": [
                    "Wide selection of {product}. Free shipping on orders over $50!",
                    "Quality {product} at competitive prices. Shop now!",
                    "Discover our premium {product} collection. Satisfaction guaranteed."
                ],
                "keywords": [
                    "buy {product}",
                    "{product} store",
                    "{product} shop",
                    "best {product}",
                    "{product} deals",
                    "{location} {product}"
                ]
            }
        }

    async def generate_campaign_preview(self, business_info: Dict, db = None) -> Dict:
        try:
            business_type = business_info.get('type', '').lower()
            business_details = {
                'cuisine': business_info.get('cuisine', '') or '',
                'location': business_info.get('location', '') or '',
                'product': business_info.get('product', '') or ''
            }

            # Seed default templates
            template = self.campaign_templates.get(business_type, self.campaign_templates['retail'])

            # Query database if session is active
            if db is not None:
                try:
                    from database.models import CampaignTemplate
                    from sqlalchemy.future import select
                    result = await db.execute(
                        select(CampaignTemplate).filter(CampaignTemplate.category == business_type)
                    )
                    db_template = result.scalars().first()
                    if db_template:
                        template = {
                            "headlines": db_template.headlines,
                            "descriptions": db_template.descriptions,
                            "keywords": db_template.keywords
                        }
                except Exception as ex:
                    logger.error(f"Error querying templates table: {ex}")

            headlines = self._format_templates(template['headlines'], business_details)
            descriptions = self._format_templates(template['descriptions'], business_details)
            keywords = self._format_templates(template['keywords'], business_details)

            return {
                "platform": "google",
                "headlines": headlines[:5],
                "descriptions": descriptions[:2],
                "keywords": keywords[:10],
                "daily_budget": business_info.get("daily_budget", 10),
                "location": business_info.get("location") or "Online",
                "estimated_metrics": self._generate_mock_metrics()
            }
        except Exception as e:
            logger.error(f"Error generating mock campaign preview: {str(e)}")
            raise

    async def create_campaign(self, campaign_data: Dict) -> Dict:
        try:
            import asyncio
            await asyncio.sleep(1)
            campaign_id = f"mock_campaign_{random.randint(1000, 9999)}"
            return {
                "platform": "google",
                "campaign_id": campaign_id,
                "status": "success",
                "preview_url": f"https://ads.google.com/mock/preview/{campaign_id}",
                "created_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error creating mock campaign: {str(e)}")
            raise

    def _format_templates(self, templates: List[str], details: Dict) -> List[str]:
        formatted = []
        for template in templates:
            try:
                formatted.append(template.format(**details))
            except KeyError:
                continue
        return formatted

    def _generate_mock_metrics(self) -> Dict:
        return {
            "impressions": random.randint(1000, 5000),
            "clicks": random.randint(50, 200),
            "ctr": round(random.uniform(1.5, 4.5), 2),
            "average_cpc": round(random.uniform(0.5, 2.5), 2),
            "cost": round(random.uniform(100, 500), 2),
            "conversions": random.randint(5, 20)
        }

class RealGoogleAdsService(AdPlatformService):
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        refresh_token = get_stored_refresh_token()
        if not refresh_token:
            logger.warning("No Google Ads refresh token found. RealGoogleAdsService operations will fail until OAuth is complete.")
            return

        config_dict = {
            "client_id": settings.google_ads_client_id,
            "client_secret": settings.google_ads_client_secret,
            "refresh_token": refresh_token,
            "developer_token": settings.google_ads_developer_token or "DUMMY_DEV_TOKEN",
            "login_customer_id": settings.google_ads_login_customer_id or "DUMMY_LOGIN_ID",
            "use_proto_plus": True
        }
        try:
            from google.ads.googleads.client import GoogleAdsClient
            self.client = GoogleAdsClient.load_from_dict(config_dict)
        except Exception as e:
            logger.error(f"Failed to initialize GoogleAdsClient: {e}")

    async def generate_campaign_preview(self, business_info: Dict, db = None) -> Dict:
        # Generate raw headlines and keywords using Mock as fallback
        mock_service = MockGoogleAdsService()
        preview = await mock_service.generate_campaign_preview(business_info, db)

        if not self.client:
            logger.warning("Google Ads Client not initialized; returning mock preview.")
            return preview

        from google.ads.googleads.errors import GoogleAdsException
        customer_id = settings.google_ads_login_customer_id or "1234567890"
        
        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.create
            campaign.name = f"Dry Run Campaign {random.randint(1000, 9999)}"
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SEARCH

            # Dry-run mutate call
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: campaign_service.mutate_campaigns(
                    customer_id=customer_id,
                    operations=[campaign_operation],
                    validate_only=True
                )
            )
            return preview
        except GoogleAdsException as e:
            formatted = handle_google_ads_error(e)
            logger.error(f"Google Ads API Dry-Run Error: {formatted}")
            raise HTTPException(status_code=400, detail=formatted)
        except Exception as e:
            logger.error(f"Unexpected Google Ads preview error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def create_campaign(self, campaign_data: Dict) -> Dict:
        if not self.client:
            raise HTTPException(status_code=400, detail="Google Ads client not initialized. Complete OAuth flow first.")

        from google.ads.googleads.errors import GoogleAdsException
        customer_id = settings.google_ads_login_customer_id or "1234567890"

        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.create
            campaign.name = campaign_data.get("campaign_name", f"Campaign {int(datetime.now().timestamp())}")
            campaign.status = self.client.enums.CampaignStatusEnum.PAUSED
            campaign.advertising_channel_type = self.client.enums.AdvertisingChannelTypeEnum.SEARCH

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: campaign_service.mutate_campaigns(
                    customer_id=customer_id,
                    operations=[campaign_operation],
                    validate_only=False
                )
            )
            created_campaign = response.results[0]
            return {
                "platform": "google",
                "campaign_id": created_campaign.resource_name,
                "status": "success",
                "preview_url": f"https://ads.google.com/aw/campaigns?ocid={customer_id}",
                "created_at": datetime.now().isoformat()
            }
        except GoogleAdsException as e:
            formatted = handle_google_ads_error(e)
            logger.error(f"Google Ads API Creation Error: {formatted}")
            raise HTTPException(status_code=400, detail=formatted)
        except Exception as e:
            logger.error(f"Unexpected Google Ads campaign creation error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

def is_google_ads_configured() -> bool:
    return bool(settings.is_google_ads_configured and get_stored_refresh_token())


def get_google_ads_service():
    if is_google_ads_configured():
        return RealGoogleAdsService()
    return MockGoogleAdsService()
