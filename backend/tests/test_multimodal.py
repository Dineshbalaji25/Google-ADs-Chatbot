import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from models.chat_model import LMStudioChatModel

@pytest.mark.asyncio
async def test_lm_studio_text_completion():
    model = LMStudioChatModel(model_name="zai-org/glm-4.7-flash", base_url="http://localhost:1234/v1")
    
    # Mock Response data
    mock_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is a text completion response."
                }
            }
        ]
    }
    
    # Patch httpx.AsyncClient.post to verify sent payload
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        # Configure Mock Response using MagicMock so json() is synchronous
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_post.return_value = mock_resp
        
        response = await model.generate_response(prompt="Hello chatbot")
        
        assert response == "This is a text completion response."
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:1234/v1/chat/completions"
        sent_payload = call_args[1]["json"]
        assert sent_payload["model"] == "zai-org/glm-4.7-flash"
        assert sent_payload["messages"] == [{"role": "user", "content": "Hello chatbot"}]

@pytest.mark.asyncio
async def test_lm_studio_vision_completion():
    model = LMStudioChatModel(model_name="zai-org/glm-4.7-flash", base_url="http://localhost:1234/v1")
    
    mock_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "The image shows a retail store."
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response
        mock_post.return_value = mock_resp
        
        # Test base64 image data
        response = await model.generate_response(
            prompt="Analyze this shop front",
            images=["iVBORw0KGgoAAAANSUhEUgAAAAUA"]
        )
        
        assert response == "The image shows a retail store."
        mock_post.assert_called_once()
        sent_payload = mock_post.call_args[1]["json"]
        assert sent_payload["messages"][0]["role"] == "user"
        content = sent_payload["messages"][0]["content"]
        assert content[0] == {"type": "text", "text": "Analyze this shop front"}
        assert content[1] == {
            "type": "image_url",
            "image_url": {
                "url": "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"
            }
        }
