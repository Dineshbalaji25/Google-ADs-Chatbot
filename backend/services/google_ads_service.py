# services/mock_google_ads_service.py
import random
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class MockGoogleAdsService:
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

    async def generate_campaign_preview(self, business_info: Dict) -> Dict:
        """Generate a mock campaign preview based on business information."""
        try:
            business_type = business_info.get('type', '').lower()
            business_details = {
                'cuisine': business_info.get('cuisine', ''),
                'location': business_info.get('location', ''),
                'product': business_info.get('product', '')
            }

            # Get template for business type or use generic template
            template = self.campaign_templates.get(business_type, self.campaign_templates['retail'])

            # Generate campaign components
            headlines = self._format_templates(template['headlines'], business_details)
            descriptions = self._format_templates(template['descriptions'], business_details)
            keywords = self._format_templates(template['keywords'], business_details)

            return {
                "headlines": headlines[:5],
                "descriptions": descriptions[:2],
                "keywords": keywords[:10],
                "estimated_metrics": self._generate_mock_metrics()
            }
        except Exception as e:
            logger.error(f"Error generating mock campaign preview: {str(e)}")
            raise

    async def create_campaign(self, campaign_data: Dict) -> Dict:
        """Create a mock campaign."""
        try:
            # Simulate API delay
            import asyncio
            await asyncio.sleep(1)

            campaign_id = f"mock_campaign_{random.randint(1000, 9999)}"
            return {
                "campaign_id": campaign_id,
                "status": "success",
                "preview_url": f"https://ads.google.com/mock/preview/{campaign_id}",
                "created_at": "2024-02-02T12:00:00Z"
            }
        except Exception as e:
            logger.error(f"Error creating mock campaign: {str(e)}")
            raise

    def _format_templates(self, templates: List[str], details: Dict) -> List[str]:
        """Format template strings with business details."""
        formatted = []
        for template in templates:
            try:
                formatted.append(template.format(**details))
            except KeyError:
                # Skip templates that can't be formatted with available details
                continue
        return formatted

    def _generate_mock_metrics(self) -> Dict:
        """Generate realistic-looking mock metrics."""
        return {
            "impressions": random.randint(1000, 5000),
            "clicks": random.randint(50, 200),
            "ctr": round(random.uniform(1.5, 4.5), 2),
            "average_cpc": round(random.uniform(0.5, 2.5), 2),
            "cost": round(random.uniform(100, 500), 2),
            "conversions": random.randint(5, 20)
        }