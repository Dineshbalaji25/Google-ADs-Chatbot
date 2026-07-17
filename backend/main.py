# main.py
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import requests
import logging
import uuid
import time

from config.config import settings
from services.google_ads_service import get_google_ads_service, save_stored_refresh_token
from services.chat_service import ChatService
from database.connection import engine, Base, get_db
from database.models import User, Campaign, Conversation, Message
from utils.auth import get_current_user, create_access_token, get_password_hash, verify_password

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# Slowapi rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Seed default templates if empty
    from sqlalchemy.orm import sessionmaker
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as db:
        from database.models import CampaignTemplate
        result = await db.execute(select(CampaignTemplate))
        count = len(result.scalars().all())
        if count == 0:
            logger.info("Seeding default campaign templates into database...")
            restaurant_template = CampaignTemplate(
                category="restaurant",
                headlines=[
                    "Best {cuisine} Restaurant in {location}",
                    "Authentic {cuisine} Dining Experience",
                    "{cuisine} Restaurant - Book Now",
                    "Delicious {cuisine} Food Near You",
                    "Top-Rated {cuisine} Restaurant"
                ],
                descriptions=[
                    "Enjoy authentic {cuisine} dishes in a wonderful atmosphere. Book your table today!",
                    "Fresh ingredients, traditional recipes. Visit us for the best {cuisine} experience.",
                    "Family-owned {cuisine} restaurant. Special deals available!"
                ],
                keywords=[
                    "{cuisine} restaurant",
                    "best {cuisine} food",
                    "{cuisine} dining",
                    "{location} {cuisine} restaurant",
                    "authentic {cuisine}",
                    "{cuisine} near me"
                ]
            )
            retail_template = CampaignTemplate(
                category="retail",
                headlines=[
                    "Quality {product} Store",
                    "Shop {product} Online",
                    "Best {product} Deals",
                    "{product} Sale - Up to 50% Off",
                    "Premium {product} Collection"
                ],
                descriptions=[
                    "Wide selection of {product}. Free shipping on orders over $50!",
                    "Quality {product} at competitive prices. Shop now!",
                    "Discover our premium {product} collection. Satisfaction guaranteed."
                ],
                keywords=[
                    "buy {product}",
                    "{product} store",
                    "{product} shop",
                    "best {product}",
                    "best {product}",
                    "{product} deals",
                    "{location} {product}"
                ]
            )
            db.add(restaurant_template)
            db.add(retail_template)
            await db.commit()
    yield

def create_app() -> FastAPI:
    app = FastAPI(title="Google Ads API", version="1.0.0", lifespan=lifespan)
    
    # Configure rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

app = create_app()

# Structured Logging and Centralized Exception Middleware
@app.middleware("http")
async def structured_logging_and_errors_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    user_id = "anonymous"
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from jose import jwt
            from utils.auth import SECRET_KEY, ALGORITHM
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub", "anonymous")
        except Exception:
            pass
            
    logger.info(f"Request started: {request.method} {request.url.path} [ID: {request_id}] [User: {user_id}]")
    
    try:
        response = await call_next(request)
        latency = time.time() - start_time
        logger.info(f"Request completed: {request.method} {request.url.path} status={response.status_code} latency={latency:.3f}s [ID: {request_id}]")
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        latency = time.time() - start_time
        logger.exception(f"Unhandled Exception in {request.method} {request.url.path} latency={latency:.3f}s [ID: {request_id}]: {e}")
        # Clean production response that does not leak internal tracebacks
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_type": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "request_id": request_id
            }
        )

# Initialize services
ads_service = get_google_ads_service()
chat_service = ChatService()

# Request/Response Schemas
class SignupRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    email: str

class ChatRequest(BaseModel):
    content: str
    session_id: Optional[str] = None

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
    location: str = "Online"

# Auth Routes
@app.post("/api/auth/signup", response_model=TokenResponse)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == payload.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already registered")
        
    hashed_pwd = get_password_hash(payload.password)
    new_user = User(email=payload.email, hashed_password=hashed_pwd)
    db.add(new_user)
    await db.flush()
    
    access_token = create_access_token(data={"sub": new_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": new_user.email
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == payload.email))
    user = result.scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email
    }

# Google Ads OAuth Redirect endpoints
@app.get("/api/auth/google/url")
async def get_google_auth_url():
    client_id = settings.google_ads_client_id
    if not client_id:
        raise HTTPException(status_code=400, detail="Google Ads Client ID is not configured.")
    redirect_uri = "http://localhost:8000/api/auth/google/callback"
    scopes = "https://www.googleapis.com/auth/adwords"
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        f"scope={scopes}&"
        "access_type=offline&"
        "prompt=consent"
    )
    return {"url": auth_url}

@app.get("/api/auth/google/callback")
async def google_auth_callback(code: str):
    client_id = settings.google_ads_client_id
    client_secret = settings.google_ads_client_secret
    if not client_id or not client_secret:
        raise HTTPException(status_code=400, detail="Google Ads credentials are not configured.")
    redirect_uri = "http://localhost:8000/api/auth/google/callback"
    
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        response = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=10)
        token_data = response.json()
        if "error" in token_data:
            raise HTTPException(status_code=400, detail=f"OAuth exchange error: {token_data.get('error_description')}")
        
        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Did not receive refresh token.")
            
        save_stored_refresh_token(refresh_token)
        
        global ads_service
        ads_service = get_google_ads_service()
        
        return RedirectResponse(url="http://localhost:3000?auth=success")
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"http://localhost:3000?auth=error&detail={str(e)}")

# Core endpoints (secured with get_current_user)
@app.post("/api/chat")
@limiter.limit("5/minute")
async def chat(
    request: Request, # required by slowapi
    chat_payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        session_id = chat_payload.session_id or "default_session"
        generator = chat_service.process_message_stream(chat_payload.content, session_id, current_user.id, db)
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        logger.error(f"Chat execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaign/preview")
async def generate_preview(
    business_info: BusinessInfo,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        preview = await ads_service.generate_campaign_preview(business_info.dict(), db)
        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaign/create")
async def create_campaign(
    campaign_payload: CampaignData,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await ads_service.create_campaign(campaign_payload.dict())
        
        # Persist Campaign to database scoped to current user
        db_campaign = Campaign(
            id=result.get("campaign_id", f"camp_{int(time.time())}"),
            user_id=current_user.id,
            name=campaign_payload.headlines[0] if campaign_payload.headlines else "Untitled Campaign",
            status="PAUSED",
            headlines=campaign_payload.headlines,
            descriptions=campaign_payload.descriptions,
            keywords=campaign_payload.keywords,
            daily_budget=campaign_payload.daily_budget,
            location=campaign_payload.location
        )
        db.add(db_campaign)
        await db.flush()
        
        return result
    except Exception as e:
        logger.error(f"Campaign creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns")
async def get_campaigns(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Campaign).filter(Campaign.user_id == current_user.id)
    )
    campaigns = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "headlines": c.headlines,
            "descriptions": c.descriptions,
            "keywords": c.keywords,
            "daily_budget": c.daily_budget,
            "location": c.location,
            "created_at": c.created_at.isoformat() if c.created_at else None
        }
        for c in campaigns
    ]

@app.get("/api/campaigns/{campaign_id}/metrics")
async def get_campaign_metrics(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Campaign).filter(Campaign.id == campaign_id, Campaign.user_id == current_user.id)
    )
    campaign = result.scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    import datetime as dt
    import random
    
    metrics_history = []
    base_date = dt.date.today() - dt.timedelta(days=7)
    
    for i in range(8):
        current_date = base_date + dt.timedelta(days=i)
        impressions = random.randint(100, 500)
        clicks = int(impressions * random.uniform(0.02, 0.08))
        ctr = round((clicks / impressions) * 100, 2) if impressions > 0 else 0.0
        avg_cpc = round(random.uniform(0.5, 2.0), 2)
        spend = round(clicks * avg_cpc, 2)
        
        metrics_history.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": ctr,
            "spend": spend,
            "cpc": avg_cpc
        })
        
    return {
        "campaign_id": campaign_id,
        "metrics": metrics_history
    }

class CampaignTemplateSchema(BaseModel):
    category: str
    headlines: List[str]
    descriptions: List[str]
    keywords: List[str]

@app.get("/api/admin/templates")
async def get_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from database.models import CampaignTemplate
    result = await db.execute(select(CampaignTemplate))
    templates = result.scalars().all()
    return [
        {
            "id": t.id,
            "category": t.category,
            "headlines": t.headlines,
            "descriptions": t.descriptions,
            "keywords": t.keywords
        }
        for t in templates
    ]

@app.post("/api/admin/templates")
async def create_template(
    payload: CampaignTemplateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from database.models import CampaignTemplate
    result = await db.execute(
        select(CampaignTemplate).filter(CampaignTemplate.category == payload.category.lower())
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Category already exists")
        
    db_template = CampaignTemplate(
        category=payload.category.lower(),
        headlines=payload.headlines,
        descriptions=payload.descriptions,
        keywords=payload.keywords
    )
    db.add(db_template)
    await db.commit()
    return {"status": "success", "id": db_template.id}

@app.put("/api/admin/templates/{template_id}")
async def update_template(
    template_id: int,
    payload: CampaignTemplateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from database.models import CampaignTemplate
    result = await db.execute(
        select(CampaignTemplate).filter(CampaignTemplate.id == template_id)
    )
    db_template = result.scalars().first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    db_template.category = payload.category.lower()
    db_template.headlines = payload.headlines
    db_template.descriptions = payload.descriptions
    db_template.keywords = payload.keywords
    
    await db.commit()
    return {"status": "success"}