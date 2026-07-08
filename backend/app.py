# app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.google_ads_service import MockGoogleAdsService
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize mock service
ads_service = MockGoogleAdsService()

class BusinessInfo(BaseModel):
    type: str
    name: str
    location: Optional[str] = None
    cuisine: Optional[str] = None
    product: Optional[str] = None
    target_audience: Optional[dict] = None
    goals: Optional[List[str]] = None

class CampaignData(BaseModel):
    headlines: List[str]
    descriptions: List[str]
    keywords: List[str]
    daily_budget: float

@app.post("/api/campaign/preview")
async def generate_preview(business_info: BusinessInfo):
    try:
        preview = await ads_service.generate_campaign_preview(business_info.dict())
        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaign/create")
async def create_campaign(campaign_data: CampaignData):
    try:
        result = await ads_service.create_campaign(campaign_data.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)