# services/chat_service.py
from models.chat_model import ChatModel

class ChatService:
    def __init__(self):
        self.chat_model = ChatModel()
        self.conversation_context = []
        
    async def process_message(self, message: str) -> dict:
        # Add business context to help guide the AI
        business_context = """
        You are an AI assistant helping to create Google Ads campaigns.
        Understand the business type and needs to suggest relevant ad content.
        """
        
        full_prompt = f"{business_context}\n\nUser: {message}\nAssistant:"
        response = await self.chat_model.generate_response(full_prompt)
        
        self.conversation_context.append({
            "role": "user",
            "content": message
        })
        self.conversation_context.append({
            "role": "assistant",
            "content": response
        })
        
        return {
            "text": response,
            "business_info": self._extract_business_info()
        }
    
    def _extract_business_info(self) -> dict:
        # Analyze conversation context to extract relevant business information
        # This is a simplified version - you'd want more sophisticated parsing
        business_info = {
            "type": "",
            "goals": [],
            "keywords": [],
            "target_audience": ""
        }
        
        # Parse conversation context to fill business_info
        # Add your parsing logic here
        
        return business_info