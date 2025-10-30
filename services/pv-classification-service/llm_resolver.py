"""
LLM Resolver
Determines active LLM provider/model and exposes options and selection APIs.

Providers:
- openai: uses OpenAI chat completions (requires OPENAI_API_KEY)
- ollama: uses local Ollama models (e.g., llama3.1:8b, phi3:mini)
"""

from typing import Dict, List, Optional
import os
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class LLMResolver:
    def __init__(self, ollama_client=None):
        self._selection: Dict[str, str] = {"provider": "ollama", "model": "llama3.1:8b"}
        self._options: List[Dict[str, str]] = []
        self._initialized = False
        self._ollama_client = ollama_client

    async def initialize(self) -> None:
        """Build available options from environment and Ollama tags."""
        if self._initialized:
            return

        options: List[Dict[str, str]] = []

        # OpenAI options (only if key exists)
        if os.getenv("OPENAI_API_KEY"):
            options.extend([
                {"provider": "openai", "model": "gpt-4"},
                {"provider": "openai", "model": "gpt-4o-mini"}
            ])

        # Ollama options - query tags if possible, else default known models
        ollama_models: List[str] = []
        try:
            if self._ollama_client is not None:
                resp = await self._ollama_client.get("/api/tags")
                if resp.status_code == 200:
                    tags = resp.json().get("models", [])
                    ollama_models = [m.get("name") for m in tags if m.get("name")]
        except Exception as e:
            logger.warning("Failed to fetch Ollama models, falling back to defaults", error=str(e))

        if not ollama_models:
            ollama_models = ["llama3.1:8b", "phi3:mini"]

        for m in ollama_models:
            options.append({"provider": "ollama", "model": m})

        self._options = options
        self._initialized = True
        logger.info("LLMResolver initialized", options=len(self._options))

    def get_options(self) -> List[Dict[str, str]]:
        return self._options

    def get_selection(self) -> Dict[str, str]:
        return self._selection

    def set_selection(self, provider: str, model: str) -> Dict[str, str]:
        # basic validation: ensure option exists
        if not any(o for o in self._options if o["provider"] == provider and o["model"] == model):
            raise ValueError(f"Requested model not available: {provider}:{model}")
        self._selection = {"provider": provider, "model": model}
        logger.info("LLM selection updated", provider=provider, model=model)
        return self._selection

    def resolve(self, override: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Return effective provider/model given an optional per-request override."""
        if override and override.get("provider") and override.get("model"):
            return {"provider": override["provider"], "model": override["model"]}
        return self._selection


# Singleton holder (filled from main.py on startup)
llm_resolver: Optional[LLMResolver] = None


