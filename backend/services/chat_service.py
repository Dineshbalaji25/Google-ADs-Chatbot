# services/chat_service.py
from models.chat_model import get_chat_model
from pydantic import BaseModel, ValidationError, field_validator
from typing import Dict, List, Literal, Optional
from sqlalchemy.future import select
from database.models import Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

logger = logging.getLogger(__name__)

class ExtractionBusinessInfo(BaseModel):
    type: str = ""
    name: str = ""
    location: Optional[str] = ""
    cuisine: Optional[str] = ""
    product: Optional[str] = ""
    target_audience: Optional[dict] = None
    goals: Optional[List[str]] = None
    platform_preference: Optional[Literal["google", "meta", "both"]] = None

    @field_validator('type', 'name', 'location', 'cuisine', 'product', mode='before')
    @classmethod
    def coerce_none_to_string(cls, v):
        if v is None:
            return ""
        return v

class ChatService:
    def __init__(self):
        self.chat_model = get_chat_model()
        
    async def process_message_stream(self, message: str, session_id: str, user_id: int, db: AsyncSession):
        # Find or create a Conversation for this user and session
        result = await db.execute(
            select(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.session_id == session_id
            )
        )
        conversation = result.scalars().first()
        
        if not conversation:
            conversation = Conversation(
                id=session_id,
                user_id=user_id,
                session_id=session_id
            )
            db.add(conversation)
            await db.flush()
            
        # Get all existing messages
        result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.id)
        )
        db_messages = result.scalars().all()
        
        # Build prompt from conversation history context
        history_str = ""
        for msg in db_messages:
            role = "User" if msg.role == "user" else "Assistant"
            history_str += f"{role}: {msg.content}\n"
            
        business_context = """
        You are an AI assistant helping to create Google and Meta ads campaigns.
        Understand the business type, platform intent, and needs to suggest relevant ad content.
        """
        
        full_prompt = f"{business_context}\n\n{history_str}User: {message}\nAssistant:"
        
        full_response = ""
        async for token in self.chat_model.generate_response_stream(full_prompt):
            full_response += token
            yield f"event: token\ndata: {json.dumps(token)}\n\n"
            
        # Save user and assistant messages to the DB
        user_msg = Message(conversation_id=conversation.id, role="user", content=message)
        assistant_msg = Message(conversation_id=conversation.id, role="assistant", content=full_response)
        db.add(user_msg)
        db.add(assistant_msg)
        await db.flush()
        
        # Extract business info
        extracted_info = await self._extract_business_info(conversation.id, db)
        user_message_count = sum(1 for msg in db_messages if msg.role == "user") + 1
        platform_selection = extracted_info.get("platform_preference")

        if not platform_selection and user_message_count >= 2:
            prompt_payload = self._platform_prompt_payload()
            extracted_info["needs_platform_selection"] = True
            yield f"event: business_info\ndata: {json.dumps(extracted_info)}\n\n"
            prompt_text = f"\n\n{prompt_payload['message']}"
            yield f"event: token\ndata: {json.dumps(prompt_text)}\n\n"
            db.add(Message(conversation_id=conversation.id, role="assistant", content=prompt_payload["message"]))
            await db.flush()
            yield f"event: platform_prompt\ndata: {json.dumps(prompt_payload)}\n\n"
            return

        platform_selection = platform_selection or "google"
        extracted_info["platform"] = platform_selection
        yield f"event: business_info\ndata: {json.dumps(extracted_info)}\n\n"

        preview = await self._generate_campaign_preview(platform_selection, extracted_info, db)
        campaign_data = self._campaign_data_from_preview(preview, platform_selection)
        yield f"event: campaign_data\ndata: {json.dumps(campaign_data)}\n\n"

    async def process_message(self, message: str, session_id: str, user_id: int, db: AsyncSession) -> dict:
        # Find or create a Conversation for this user and session
        result = await db.execute(
            select(Conversation).filter(
                Conversation.user_id == user_id,
                Conversation.session_id == session_id
            )
        )
        conversation = result.scalars().first()
        
        if not conversation:
            conversation = Conversation(
                id=session_id, # Use session_id as the unique conversation identifier
                user_id=user_id,
                session_id=session_id
            )
            db.add(conversation)
            await db.flush()
            
        # Get all existing messages
        result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.id)
        )
        db_messages = result.scalars().all()
        
        # Build prompt from conversation history context
        history_str = ""
        for msg in db_messages:
            role = "User" if msg.role == "user" else "Assistant"
            history_str += f"{role}: {msg.content}\n"
            
        business_context = """
        You are an AI assistant helping to create Google and Meta ads campaigns.
        Understand the business type, platform intent, and needs to suggest relevant ad content.
        """
        
        full_prompt = f"{business_context}\n\n{history_str}User: {message}\nAssistant:"
        response = await self.chat_model.generate_response(full_prompt)
        
        # Save user and assistant messages to the DB
        user_msg = Message(conversation_id=conversation.id, role="user", content=message)
        assistant_msg = Message(conversation_id=conversation.id, role="assistant", content=response)
        db.add(user_msg)
        db.add(assistant_msg)
        await db.flush()
        
        # Extract business info using structured output
        extracted_info = await self._extract_business_info(conversation.id, db)
        
        return {
            "text": response,
            "business_info": extracted_info
        }
    
    async def _generate_campaign_preview(self, platform_selection: str, extracted_info: Dict, db: AsyncSession) -> Dict:
        from services.ad_platform_service import expand_platform_selection, get_ad_platform_service

        platforms = expand_platform_selection(platform_selection)
        if len(platforms) == 1:
            platform = platforms[0]
            preview = await get_ad_platform_service(platform).generate_campaign_preview({**extracted_info, "platform": platform}, db)
            preview.setdefault("platform", platform)
            return preview

        previews = {}
        for platform in platforms:
            preview = await get_ad_platform_service(platform).generate_campaign_preview({**extracted_info, "platform": platform}, db)
            preview.setdefault("platform", platform)
            previews[platform] = preview
        return {"platform": "both", "previews": previews}

    def _campaign_data_from_preview(self, preview: Dict, platform_selection: str) -> Dict:
        if platform_selection == "both":
            previews = preview.get("previews", {})
            google_preview = previews.get("google", {})
            meta_preview = previews.get("meta", {})
            return {
                "platform": "both",
                "previews": previews,
                "headlines": google_preview.get("headlines", []),
                "description": self._first(google_preview, "descriptions"),
                "descriptions": google_preview.get("descriptions", []),
                "keywords": google_preview.get("keywords", []),
                "primary_text": meta_preview.get("primary_text") or self._first(meta_preview, "primary_texts"),
                "primary_texts": meta_preview.get("primary_texts", []),
                "page_id": meta_preview.get("page_id"),
                "call_to_action": meta_preview.get("call_to_action"),
                "asset_url": meta_preview.get("asset_url"),
                "link_url": meta_preview.get("link_url"),
                "estimated_metrics": {
                    "google": google_preview.get("estimated_metrics", {}),
                    "meta": meta_preview.get("estimated_metrics", {}),
                },
                "daily_budget": google_preview.get("daily_budget") or meta_preview.get("daily_budget", 10),
                "location": google_preview.get("location") or meta_preview.get("location", "Online"),
            }

        return {
            "platform": platform_selection,
            "headlines": preview.get("headlines", []),
            "description": preview.get("description") or self._first(preview, "descriptions"),
            "descriptions": preview.get("descriptions", []),
            "keywords": preview.get("keywords", []),
            "primary_text": preview.get("primary_text") or self._first(preview, "primary_texts"),
            "primary_texts": preview.get("primary_texts", []),
            "page_id": preview.get("page_id"),
            "call_to_action": preview.get("call_to_action"),
            "asset_url": preview.get("asset_url"),
            "link_url": preview.get("link_url"),
            "estimated_metrics": preview.get("estimated_metrics", {}),
            "daily_budget": preview.get("daily_budget", 10),
            "location": preview.get("location", "Online"),
        }

    def _first(self, payload: Dict, key: str) -> str:
        values = payload.get(key) or []
        return values[0] if values else ""

    def _platform_prompt_payload(self) -> Dict:
        return {
            "message": "Which ad platform should we use for this campaign?",
            "options": [
                {"label": "Google", "value": "google", "content": "Use Google Ads"},
                {"label": "Meta", "value": "meta", "content": "Use Meta Ads"},
                {"label": "Both", "value": "both", "content": "Use both Google and Meta Ads"},
            ],
        }

    async def _extract_business_info(self, conversation_id: str, db: AsyncSession) -> dict:
        # Get all messages in conversation
        result = await db.execute(
            select(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id)
        )
        db_messages = result.scalars().all()
        
        history_str = ""
        for msg in db_messages:
            role = "User" if msg.role == "user" else "Assistant"
            history_str += f"{role}: {msg.content}\n"
            
        prompt = f"""
You are an information extraction assistant. Read the following conversation history and extract the business details as a valid JSON object matching this schema:
{{
  "type": "restaurant or retail",
  "name": "name of the business",
  "location": "geographic location (e.g. 'New York', 'Online')",
  "cuisine": "cuisine type (only if type is restaurant)",
  "product": "product sold (only if type is retail)",
  "target_audience": {{}},
  "goals": [],
  "platform_preference": "google or meta or both or null"
}}

Return ONLY the raw JSON block. Do not write any explanations, markdown wrappers, or conversational text.

Conversation history:
{history_str}
"""
        # Default fallback stub
        fallback_stub = {
            "type": "retail",
            "name": "Default Business",
            "location": "Online",
            "cuisine": None,
            "product": "Premium Goods",
            "target_audience": {},
            "goals": [],
            "platform_preference": None
        }
        
        # Perform extraction with retry-once logic
        for attempt in range(2):
            response_text = None
            try:
                if hasattr(self.chat_model, 'is_mock') and self.chat_model.is_mock:
                    return self._extract_business_info_heuristic(db_messages)
                    
                response_text = await self.chat_model.generate_response(prompt)
                
                cleaned_text = response_text.strip()
                if cleaned_text.startswith("```"):
                    lines = cleaned_text.splitlines()
                    if len(lines) > 2:
                        cleaned_text = "\n".join(lines[1:-1]).strip()
                
                parsed_json = json.loads(cleaned_text)
                validated_model = ExtractionBusinessInfo(**parsed_json)
                return validated_model.model_dump()
                
            except (json.JSONDecodeError, ValidationError, Exception) as e:
                logger.warning(f"Structured extraction attempt {attempt + 1} failed: {e}. Raw response: {repr(response_text)}")
                if attempt == 1:
                    logger.error("Structured business extraction failed twice. Falling back to heuristic.")
                    return self._extract_business_info_heuristic(db_messages)
        
        return fallback_stub

    def _extract_business_info_heuristic(self, db_messages: List[Message]) -> dict:
        """Fallback heuristic method for local/mock development."""
        business_info = {
            "type": "retail",
            "name": "Default Business",
            "location": "Online",
            "cuisine": None,
            "product": "Premium Goods",
            "target_audience": {},
            "goals": [],
            "platform_preference": None
        }
        
        for msg in db_messages:
            if msg.role == "user":
                content_lower = msg.content.lower()
                if any(w in content_lower for w in ["both google and meta", "google and meta", "both platforms", "both ads"]):
                    business_info["platform_preference"] = "both"
                elif any(w in content_lower for w in ["meta", "facebook", "instagram"]):
                    business_info["platform_preference"] = "meta"
                elif any(w in content_lower for w in ["google", "search ads", "search campaign"]):
                    business_info["platform_preference"] = "google"

                if any(w in content_lower for w in ["restaurant", "cafe", "dining", "eatery", "food"]):
                    business_info["type"] = "restaurant"
                    if "pizza" in content_lower:
                        business_info["cuisine"] = "pizza"
                    elif "italian" in content_lower:
                        business_info["cuisine"] = "italian"
                    elif "mexican" in content_lower:
                        business_info["cuisine"] = "mexican"
                    else:
                        business_info["cuisine"] = "general"
                elif any(w in content_lower for w in ["shop", "retail", "store", "product", "sell", "goods"]):
                    business_info["type"] = "retail"
                    if "shoes" in content_lower:
                        business_info["product"] = "shoes"
                    elif "clothing" in content_lower or "clothes" in content_lower:
                        business_info["product"] = "clothing"
                
                if "in " in content_lower:
                    parts = content_lower.split("in ")
                    if len(parts) > 1:
                        loc = parts[1].split()[0].strip(",.!?;:")
                        business_info["location"] = loc.capitalize()
                        
                if "called " in content_lower:
                    parts = content_lower.split("called ")
                    if len(parts) > 1:
                        business_info["name"] = parts[1].split("\n")[0].strip(",.!?;:")
                elif "named " in content_lower:
                    parts = content_lower.split("named ")
                    if len(parts) > 1:
                        business_info["name"] = parts[1].split("\n")[0].strip(",.!?;:")

        return business_info