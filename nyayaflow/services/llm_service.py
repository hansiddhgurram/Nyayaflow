"""LLM service using Ollama with Gemma models."""
import os
import json
import httpx
from typing import Optional, Dict, Any
from backend.config import get_settings

settings = get_settings()


class LLMService:
    """Interface to local Ollama LLM (Gemma)."""

    def __init__(self, model: Optional[str] = None, host: Optional[str] = None):
        self.model = model or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """Generate text from LLM."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are a helpful legal assistant for Indian dispute resolution. Be precise, factual, and cite Indian statutes where applicable. Never make binding legal determinations.",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except httpx.HTTPError as e:
            raise Exception(f"LLM inference failed: {e}")

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> Dict[str, Any]:
        """Generate and parse JSON from LLM."""
        text = await self.generate(prompt, system_prompt, temperature)
        # Clean up markdown code blocks
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: try to extract JSON-like structure
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise Exception(f"Failed to parse JSON from LLM response: {text[:200]}")

    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 2048) -> str:
        """Synchronous wrapper for non-async contexts."""
        import requests
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt or "You are a helpful legal assistant for Indian dispute resolution. Be precise, factual, and cite Indian statutes where applicable. Never make binding legal determinations.",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.RequestException as e:
            raise Exception(f"LLM inference failed: {e}")
