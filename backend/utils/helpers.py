# utils/helpers.py
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from google.ads.googleads.errors import GoogleAdsException

logger = logging.getLogger(__name__)

def format_ad_preview(preview_data: Dict) -> Dict:
    """Format the ad preview data for frontend display."""
    try:
        return {
            "headlines": preview_data.get("headlines", [])[:3],
            "descriptions": preview_data.get("descriptions", [])[:2],
            "keywords": format_keywords(preview_data.get("keywords", [])),
            "metrics": format_metrics(preview_data.get("estimated_metrics", {}))
        }
    except Exception as e:
        logger.error(f"Error formatting ad preview: {str(e)}")
        return {}

def format_keywords(keywords: List[str], max_keywords: int = 20) -> List[Dict]:
    """Format keywords with additional metadata."""
    try:
        formatted_keywords = []
        for keyword in keywords[:max_keywords]:
            formatted_keywords.append({
                "text": keyword,
                "match_type": suggest_match_type(keyword),
                "estimated_clicks": calculate_estimated_clicks(keyword)
            })
        return formatted_keywords
    except Exception as e:
        logger.error(f"Error formatting keywords: {str(e)}")
        return []

def format_metrics(metrics: Dict) -> Dict:
    """Format estimated metrics for display."""
    try:
        return {
            "clicks": format_number(metrics.get("clicks", 0)),
            "impressions": format_number(metrics.get("impressions", 0)),
            "ctr": format_percentage(metrics.get("ctr", 0)),
            "average_cpc": format_currency(metrics.get("average_cpc", 0))
        }
    except Exception as e:
        logger.error(f"Error formatting metrics: {str(e)}")
        return {}

def suggest_match_type(keyword: str) -> str:
    """Suggest a match type for a keyword."""
    keyword = keyword.lower().strip()
    if ' ' not in keyword:
        return 'exact'
    elif len(keyword.split()) > 3:
        return 'phrase'
    return 'broad'

def calculate_estimated_clicks(keyword: str) -> int:
    """Calculate estimated clicks based on keyword characteristics."""
    # This is a simplified example - in reality, you'd use Google Ads API
    base_clicks = 100
    word_count = len(keyword.split())
    return int(base_clicks / word_count)

def format_number(number: int) -> str:
    """Format large numbers for display."""
    if number >= 1000000:
        return f"{number/1000000:.1f}M"
    elif number >= 1000:
        return f"{number/1000:.1f}K"
    return str(number)

def format_percentage(value: float) -> str:
    """Format percentage values."""
    return f"{value:.2f}%"

def format_currency(amount: float) -> str:
    """Format currency values."""
    return f"${amount:.2f}"

def handle_google_ads_error(error: GoogleAdsException) -> Dict:
    """Handle Google Ads API errors."""
    error_details = []
    
    for error in error.failure.errors:
        error_details.append({
            "error_code": error.error_code.enum_name,
            "message": error.message,
            "trigger": {
                "field_path_elements": [
                    {
                        "field_name": element.field_name,
                        "index": element.index
                    }
                    for element in error.location.field_path_elements
                ]
            }
        })
    
    return {
        "error_type": "GOOGLE_ADS_API_ERROR",
        "timestamp": datetime.now().isoformat(),
        "details": error_details
    }

def validate_campaign_data(campaign_data: Dict) -> Optional[Dict]:
    """Validate campaign data before creation."""
    required_fields = [
        "campaign_name",
        "budget_amount",
        "headlines",
        "descriptions",
        "keywords"
    ]
    
    missing_fields = [field for field in required_fields if field not in campaign_data]
    
    if missing_fields:
        return {
            "valid": False,
            "missing_fields": missing_fields,
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    if not (1 <= len(campaign_data["headlines"]) <= 15):
        return {
            "valid": False,
            "message": "Number of headlines must be between 1 and 15"
        }
    
    if not (1 <= len(campaign_data["descriptions"]) <= 4):
        return {
            "valid": False,
            "message": "Number of descriptions must be between 1 and 4"
        }
    
    return None  # None indicates validation passed

def generate_tracking_template(campaign_type: str, parameters: Dict) -> str:
    """Generate tracking template for campaign URLs."""
    base_template = "{lpurl}?"
    tracking_params = []
    
    # Add standard UTM parameters
    tracking_params.extend([
        f"utm_source=google",
        f"utm_medium=cpc",
        f"utm_campaign={parameters.get('campaign_name', '')}"
    ])
    
    # Add custom parameters based on campaign type
    if campaign_type == "dynamic":
        tracking_params.extend([
            "keyword={keyword}",
            "matchtype={matchtype}",
            "device={device}"
        ])
    
    return base_template + "&".join(tracking_params)

def clean_keyword_text(keyword: str) -> str:
    """Clean and format keyword text."""
    # Remove multiple spaces
    keyword = " ".join(keyword.split())
    # Remove special characters
    keyword = "".join(c for c in keyword if c.isalnum() or c.isspace())
    # Convert to lowercase
    keyword = keyword.lower()
    return keyword