import logging
import os
import json
import httpx
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List
from config.config import settings

logger = logging.getLogger(__name__)

class ChatModel(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, images: Optional[List[str]] = None) -> str:
        """Generate full response synchronously."""
        pass

    @abstractmethod
    async def generate_response_stream(self, prompt: str, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        """Generate response as an async stream of tokens."""
        pass

class GeminiChatModel(ChatModel):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_response(self, prompt: str, images: Optional[List[str]] = None) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        parts = [{"text": prompt}]
        if images:
            for img in images:
                if img.startswith("data:"):
                    try:
                        header, base64_data = img.split(",", 1)
                        mime_type = header.split(";")[0].split(":")[1]
                    except Exception:
                        mime_type = "image/jpeg"
                        base64_data = img
                else:
                    mime_type = "image/jpeg"
                    base64_data = img
                parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_data
                    }
                })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_tokens
            }
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    logger.error(f"Gemini API error ({response.status_code}): {response.text}")
                    raise Exception(f"Gemini API error: {response.text}")
        except Exception as e:
            logger.error(f"Gemini generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        
        parts = [{"text": prompt}]
        if images:
            for img in images:
                if img.startswith("data:"):
                    try:
                        header, base64_data = img.split(",", 1)
                        mime_type = header.split(";")[0].split(":")[1]
                    except Exception:
                        mime_type = "image/jpeg"
                        base64_data = img
                else:
                    mime_type = "image/jpeg"
                    base64_data = img
                parts.append({
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64_data
                    }
                })

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_tokens
            }
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        buffer = ""
                        async for line in response.aiter_lines():
                            if line:
                                buffer += line + "\n"
                                while True:
                                    start = buffer.find("{")
                                    if start == -1:
                                        break
                                    
                                    depth = 0
                                    end = -1
                                    in_string = False
                                    escape = False
                                    for i in range(start, len(buffer)):
                                        char = buffer[i]
                                        if escape:
                                            escape = False
                                            continue
                                        if char == "\\":
                                            escape = True
                                            continue
                                        if char == '"':
                                            in_string = not in_string
                                            continue
                                        if not in_string:
                                            if char == "{":
                                                depth += 1
                                            elif char == "}":
                                                depth -= 1
                                                if depth == 0:
                                                    end = i
                                                    break
                                    
                                    if end != -1:
                                        json_str = buffer[start:end+1]
                                        buffer = buffer[end+1:]
                                        try:
                                            chunk = json.loads(json_str)
                                            if "candidates" in chunk and chunk["candidates"]:
                                                content = chunk["candidates"][0].get("content", {})
                                                parts = content.get("parts", [])
                                                if parts and "text" in parts[0]:
                                                    text = parts[0]["text"]
                                                    if text:
                                                        yield text
                                        except Exception:
                                            pass
                                    else:
                                        break
                    else:
                        error_text = await response.aread()
                        logger.error(f"Gemini stream error ({response.status_code}): {error_text.decode('utf-8')}")
                        yield f"Error calling Gemini stream: {response.status_code}"
        except Exception as e:
            logger.error(f"Gemini stream exception: {e}")
            yield f"Exception during Gemini stream: {e}"

class OpenAIChatModel(ChatModel):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_response(self, prompt: str, images: Optional[List[str]] = None) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if images:
            content_blocks = [{"type": "text", "text": prompt}]
            for img in images:
                if not (img.startswith("data:") or img.startswith("http")):
                    img_url = f"data:image/jpeg;base64,{img}"
                else:
                    img_url = img
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                })
            messages = [{"role": "user", "content": content_blocks}]
        else:
            messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenAI API error ({response.status_code}): {response.text}")
                    raise Exception(f"OpenAI API error: {response.text}")
        except Exception as e:
            logger.error(f"OpenAI generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if images:
            content_blocks = [{"type": "text", "text": prompt}]
            for img in images:
                if not (img.startswith("data:") or img.startswith("http")):
                    img_url = f"data:image/jpeg;base64,{img}"
                else:
                    img_url = img
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                })
            messages = [{"role": "user", "content": content_blocks}]
        else:
            messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                line_str = line.strip()
                                if line_str.startswith("data: "):
                                    content = line_str[6:]
                                    if content == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(content)
                                        text = chunk["choices"][0]["delta"].get("content", "")
                                        if text:
                                            yield text
                                    except Exception:
                                        pass
                    else:
                        error_text = await response.aread()
                        logger.error(f"OpenAI stream error ({response.status_code}): {error_text.decode('utf-8')}")
                        yield f"Error calling OpenAI stream: {response.status_code}"
        except Exception as e:
            logger.error(f"OpenAI stream exception: {e}")
            yield f"Exception during OpenAI stream: {e}"

class AnthropicChatModel(ChatModel):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_response(self, prompt: str, images: Optional[List[str]] = None) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        content_blocks = [{"type": "text", "text": prompt}]
        if images:
            for img in images:
                if img.startswith("data:"):
                    try:
                        header, base64_data = img.split(",", 1)
                        media_type = header.split(";")[0].split(":")[1]
                    except Exception:
                        media_type = "image/jpeg"
                        base64_data = img
                else:
                    media_type = "image/jpeg"
                    base64_data = img
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data
                    }
                })
        payload = {
            "model": self.model_name,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "messages": [{"role": "user", "content": content_blocks}]
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["content"][0]["text"]
                else:
                    logger.error(f"Anthropic API error ({response.status_code}): {response.text}")
                    raise Exception(f"Anthropic API error: {response.text}")
        except Exception as e:
            logger.error(f"Anthropic generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        content_blocks = [{"type": "text", "text": prompt}]
        if images:
            for img in images:
                if img.startswith("data:"):
                    try:
                        header, base64_data = img.split(",", 1)
                        media_type = header.split(";")[0].split(":")[1]
                    except Exception:
                        media_type = "image/jpeg"
                        base64_data = img
                else:
                    media_type = "image/jpeg"
                    base64_data = img
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": base64_data
                    }
                })
        payload = {
            "model": self.model_name,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "messages": [{"role": "user", "content": content_blocks}],
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                line_str = line.strip()
                                if line_str.startswith("data: "):
                                    content = line_str[6:]
                                    try:
                                        chunk = json.loads(content)
                                        if chunk.get("type") == "content_block_delta":
                                            text = chunk["delta"].get("text", "")
                                            if text:
                                                yield text
                                    except Exception:
                                        pass
                    else:
                        error_text = await response.aread()
                        logger.error(f"Anthropic stream error ({response.status_code}): {error_text.decode('utf-8')}")
                        yield f"Error calling Anthropic stream: {response.status_code}"
        except Exception as e:
            logger.error(f"Anthropic stream exception: {e}")
            yield f"Exception during Anthropic stream: {e}"

class MockChatModel(ChatModel):
    is_mock = True

    async def generate_response(self, prompt: str, images: Optional[List[str]] = None) -> str:
        # Extract user query to reply intelligently
        user_msg = "your business"
        if "User:" in prompt:
            user_msg = prompt.split("User:")[-1].split("Assistant:")[0].strip()
        
        user_msg_lower = user_msg.lower()
        if "restaurant" in user_msg_lower or "pizza" in user_msg_lower or "food" in user_msg_lower:
            return "I can help you build an ad campaign for your restaurant! What is the name of your restaurant, and what location or cuisine do you want to target?"
        elif "shoes" in user_msg_lower or "clothing" in user_msg_lower or "retail" in user_msg_lower:
            return "I'd love to help you set up Google Ads for your retail shop! What products do you sell, and are you targeting a specific location or online?"
        else:
            return f"I can help you create a Google Ads campaign. Tell me more about your business (is it a restaurant, store, etc.?) and what you're advertising."

    async def generate_response_stream(self, prompt: str, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        response = await self.generate_response(prompt, images)
        for word in response.split(" "):
            yield word + " "
            await asyncio.sleep(0.05)

class LMStudioChatModel(ChatModel):
    def __init__(self, model_name: str, base_url: str):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    async def _resolve_model_name(self, client: httpx.AsyncClient) -> str:
        if self.model_name and self.model_name not in ("local-model", "gemini-3.5-flash", "default"):
            return self.model_name
        try:
            res = await client.get(f"{self.base_url}/models")
            if res.status_code == 200:
                data = res.json().get("data", [])
                for m in data:
                    m_id = m.get("id", "")
                    if "embed" not in m_id.lower():
                        return m_id
                if data:
                    return data[0].get("id", self.model_name)
        except Exception as e:
            logger.warning(f"Could not auto-detect LM Studio model name: {e}")
        return self.model_name

    async def generate_response(self, prompt: str, images: Optional[List[str]] = None) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if images:
            content_blocks = [{"type": "text", "text": prompt}]
            for img in images:
                if not (img.startswith("data:") or img.startswith("http")):
                    img_url = f"data:image/jpeg;base64,{img}"
                else:
                    img_url = img
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                })
            messages = [{"role": "user", "content": content_blocks}]
        else:
            messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload["model"] = await self._resolve_model_name(client)
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    res_data = response.json()
                    return res_data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"LM Studio API error ({response.status_code}): {response.text}")
                    raise Exception(f"LM Studio API error: {response.text}")
        except Exception as e:
            logger.error(f"LM Studio generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str, images: Optional[List[str]] = None) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if images:
            content_blocks = [{"type": "text", "text": prompt}]
            for img in images:
                if not (img.startswith("data:") or img.startswith("http")):
                    img_url = f"data:image/jpeg;base64,{img}"
                else:
                    img_url = img
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {
                        "url": img_url
                    }
                })
            messages = [{"role": "user", "content": content_blocks}]
        else:
            messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "stream": True
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload["model"] = await self._resolve_model_name(client)
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line:
                                line_str = line.strip()
                                if line_str.startswith("data: "):
                                    content = line_str[6:]
                                    if content == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(content)
                                        text = chunk["choices"][0]["delta"].get("content", "")
                                        if text:
                                            yield text
                                    except Exception:
                                        pass
                    else:
                        error_text = await response.aread()
                        logger.error(f"LM Studio stream error ({response.status_code}): {error_text.decode('utf-8')}")
                        yield f"Error calling LM Studio stream: {response.status_code}"
        except Exception as e:
            logger.error(f"LM Studio stream exception: {e}")
            yield f"Exception during LM Studio stream: {e}"

def get_chat_model() -> ChatModel:
    provider = settings.model_provider.lower()
    
    if provider == "mock":
        return MockChatModel()
        
    if provider in ("lm_studio", "lmstudio", "local"):
        model_name = settings.model_name if settings.model_name and settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "local-model"
        return LMStudioChatModel(model_name, settings.lm_studio_base_url)
    
    api_key = settings.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    
    if provider == "gemini":
        if not api_key:
            raise ValueError("Gemini API key is not configured. Please set API_KEY or GEMINI_API_KEY in the environment or .env file.")
        model_name = settings.model_name if settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "gemini-1.5-flash"
        return GeminiChatModel(api_key, model_name)
    elif provider == "openai":
        if not api_key:
            raise ValueError("OpenAI API key is not configured. Please set API_KEY or OPENAI_API_KEY in the environment or .env file.")
        model_name = settings.model_name if settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "gpt-4o-mini"
        return OpenAIChatModel(api_key, model_name)
    elif provider == "anthropic":
        if not api_key:
            raise ValueError("Anthropic API key is not configured. Please set API_KEY or ANTHROPIC_API_KEY in the environment or .env file.")
        model_name = settings.model_name if settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "claude-3-5-sonnet-20240620"
        return AnthropicChatModel(api_key, model_name)
    
    raise ValueError(f"Unsupported model provider: {provider}")