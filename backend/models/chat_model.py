import logging
import os
import json
import requests
import asyncio
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from config.config import settings

logger = logging.getLogger(__name__)

class ChatModel(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        """Generate full response synchronously."""
        pass

    @abstractmethod
    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Generate response as an async stream of tokens."""
        pass

class GeminiChatModel(ChatModel):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_response(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_tokens
            }
        }
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=payload, timeout=30)
            )
            if response.status_code == 200:
                res_data = response.json()
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.error(f"Gemini API error ({response.status_code}): {response.text}")
                raise Exception(f"Gemini API error: {response.text}")
        except Exception as e:
            logger.error(f"Gemini generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_tokens
            }
        }
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
            )
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').strip()
                        # Gemini stream sends items wrapped in brackets/commas
                        if line_str.startswith("["):
                            line_str = line_str[1:]
                        if line_str.endswith("]"):
                            line_str = line_str[:-1]
                        if line_str.startswith(","):
                            line_str = line_str[1:]
                        line_str = line_str.strip()
                        if line_str:
                            try:
                                chunk = json.loads(line_str)
                                text = chunk["candidates"][0]["content"]["parts"][0]["text"]
                                yield text
                            except Exception:
                                pass
                            await asyncio.sleep(0.01)
            else:
                logger.error(f"Gemini stream error ({response.status_code}): {response.text}")
                yield f"Error calling Gemini stream: {response.status_code}"
        except Exception as e:
            logger.error(f"Gemini stream exception: {e}")
            yield f"Exception during Gemini stream: {e}"

class OpenAIChatModel(ChatModel):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_response(self, prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=payload, timeout=30)
            )
            if response.status_code == 200:
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenAI API error ({response.status_code}): {response.text}")
                raise Exception(f"OpenAI API error: {response.text}")
        except Exception as e:
            logger.error(f"OpenAI generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "stream": True
        }
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
            )
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').strip()
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
                            await asyncio.sleep(0.01)
            else:
                logger.error(f"OpenAI stream error ({response.status_code}): {response.text}")
                yield f"Error calling OpenAI stream: {response.status_code}"
        except Exception as e:
            logger.error(f"OpenAI stream exception: {e}")
            yield f"Exception during OpenAI stream: {e}"

class AnthropicChatModel(ChatModel):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name

    async def generate_response(self, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=payload, timeout=30)
            )
            if response.status_code == 200:
                res_data = response.json()
                return res_data["content"][0]["text"]
            else:
                logger.error(f"Anthropic API error ({response.status_code}): {response.text}")
                raise Exception(f"Anthropic API error: {response.text}")
        except Exception as e:
            logger.error(f"Anthropic generation exception: {e}")
            raise

    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, headers=headers, json=payload, stream=True, timeout=30)
            )
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8').strip()
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
                            await asyncio.sleep(0.01)
            else:
                logger.error(f"Anthropic stream error ({response.status_code}): {response.text}")
                yield f"Error calling Anthropic stream: {response.status_code}"
        except Exception as e:
            logger.error(f"Anthropic stream exception: {e}")
            yield f"Exception during Anthropic stream: {e}"

class MockChatModel(ChatModel):
    async def generate_response(self, prompt: str) -> str:
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

    async def generate_response_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        response = await self.generate_response(prompt)
        for word in response.split(" "):
            yield word + " "
            await asyncio.sleep(0.05)

def get_chat_model() -> ChatModel:
    provider = settings.model_provider.lower()
    api_key = settings.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    
    if provider == "gemini":
        if not api_key:
            logger.warning("Gemini API key is not configured. Falling back to MockChatModel.")
            return MockChatModel()
        model_name = settings.model_name if settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "gemini-1.5-flash"
        return GeminiChatModel(api_key, model_name)
    elif provider == "openai":
        if not api_key:
            logger.warning("OpenAI API key is not configured. Falling back to MockChatModel.")
            return MockChatModel()
        model_name = settings.model_name if settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "gpt-4o-mini"
        return OpenAIChatModel(api_key, model_name)
    elif provider == "anthropic":
        if not api_key:
            logger.warning("Anthropic API key is not configured. Falling back to MockChatModel.")
            return MockChatModel()
        model_name = settings.model_name if settings.model_name != "deepseek-ai/deepseek-coder-6.7b-base" else "claude-3-5-sonnet-20240620"
        return AnthropicChatModel(api_key, model_name)
    
    return MockChatModel()