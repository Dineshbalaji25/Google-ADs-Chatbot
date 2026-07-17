# services/chat_service.py
from models.chat_model import get_chat_model
from pydantic import BaseModel, ValidationError
from typing import Dict, List, Optional
from sqlalchemy.future import select
from database.models import Conversation, Message
from sqlalchemy.ext.asyncio import AsyncSession
import json
import logging

logger = logging.getLogger(__name__)

class ExtractionBusinessInfo(BaseModel):
    type: str
    name: str
    location: Optional[str] = None
    cuisine: Optional[str] = None
    product: Optional[str] = None
    target_audience: Optional[dict] = None
    goals: Optional[List[str]] = None

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
        You are an AI assistant helping to create Google Ads campaigns.
        Understand the business type and needs to suggest relevant ad content.
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
        yield f"event: business_info\ndata: {json.dumps(extracted_info)}\n\n"
        
        # Generate campaign preview
        from services.google_ads_service import get_google_ads_service
        ads_service = get_google_ads_service()
        preview = await ads_service.generate_campaign_preview(extracted_info, db)
        
        campaign_data = {
            "headlines": preview.get("headlines", []),
            "description": preview.get("descriptions", [""])[0] if preview.get("descriptions") else "",
            "descriptions": preview.get("descriptions", []),
            "keywords": preview.get("keywords", []),
            "estimated_metrics": preview.get("estimated_metrics", {}),
            "daily_budget": preview.get("daily_budget", 10),
            "location": preview.get("location", "Online")
        }
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
        You are an AI assistant helping to create Google Ads campaigns.
        Understand the business type and needs to suggest relevant ad content.
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
  "type": "restaurant" or "retail",
  "name": "name of the business",
  "location": "geographic location (e.g. 'New York', 'Online')",
  "cuisine": "cuisine type (only if type is restaurant)",
  "product": "product sold (only if type is retail)",
  "target_audience": {{}},
  "goals": []
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
            "goals": []
        }
        
        # Perform extraction with retry-once logic
        for attempt in range(2):
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
                return validated_model.dict()
                
            except (json.JSONDecodeError, ValidationError, Exception) as e:
                logger.warning(f"Structured extraction attempt {attempt + 1} failed: {e}")
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
            "goals": []
        }
        
        for msg in db_messages:
            if msg.role == "user":
                content_lower = msg.content.lower()
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