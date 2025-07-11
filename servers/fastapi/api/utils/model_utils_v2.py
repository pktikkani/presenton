"""Enhanced model utilities for V2 with dynamic model selection"""
import os
from typing import List, Optional, Dict, Set
import aiohttp
from functools import lru_cache
import asyncio

from openai import AsyncOpenAI
from api.models import SelectedLLMProvider
from api.utils.model_utils import (
    get_selected_llm_provider,
    get_llm_api_key,
    get_model_base_url,
    get_llm_client
)


class ModelManagerV2:
    """Enhanced model manager with dynamic model selection and validation"""
    
    def __init__(self):
        self._model_cache: Dict[str, Set[str]] = {}
        self._cache_ttl = 3600  # 1 hour cache
        self._last_cache_time: Dict[str, float] = {}
    
    async def get_available_openai_models(self, force_refresh: bool = False) -> Set[str]:
        """Get list of available OpenAI models with caching"""
        cache_key = "openai"
        
        # Check cache
        if not force_refresh and cache_key in self._model_cache:
            if asyncio.get_event_loop().time() - self._last_cache_time.get(cache_key, 0) < self._cache_ttl:
                return self._model_cache[cache_key]
        
        api_key = get_llm_api_key()
        if not api_key:
            return self._get_default_openai_models()
        
        try:
            client = AsyncOpenAI(api_key=api_key)
            models = []
            async for model in client.models.list():
                models.append(model.id)
            
            # Filter for GPT models
            gpt_models = {m for m in models if m.startswith(('gpt-4', 'gpt-3.5'))}
            
            # Cache the results
            self._model_cache[cache_key] = gpt_models
            self._last_cache_time[cache_key] = asyncio.get_event_loop().time()
            
            return gpt_models
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            return self._get_default_openai_models()
    
    async def get_available_google_models(self, force_refresh: bool = False) -> Set[str]:
        """Get list of available Google/Gemini models"""
        cache_key = "google"
        
        # Check cache
        if not force_refresh and cache_key in self._model_cache:
            if asyncio.get_event_loop().time() - self._last_cache_time.get(cache_key, 0) < self._cache_ttl:
                return self._model_cache[cache_key]
        
        api_key = get_llm_api_key()
        if not api_key:
            return self._get_default_google_models()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = set()
                        for model in data.get("models", []):
                            model_name = model.get("name", "").replace("models/", "")
                            if model_name:
                                models.add(model_name)
                        
                        # Cache the results
                        self._model_cache[cache_key] = models
                        self._last_cache_time[cache_key] = asyncio.get_event_loop().time()
                        
                        return models
        except Exception as e:
            print(f"Error fetching Google models: {e}")
        
        return self._get_default_google_models()
    
    def _get_default_openai_models(self) -> Set[str]:
        """Default OpenAI models when API call fails"""
        return {
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        }
    
    def _get_default_google_models(self) -> Set[str]:
        """Default Google models when API call fails"""
        return {
            "gemini-2.0-flash-preview",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-pro",
            "gemini-pro-vision"
        }
    
    async def validate_model(self, model: Optional[str], provider: Optional[SelectedLLMProvider] = None) -> str:
        """Validate and return the model string"""
        if provider is None:
            provider = get_selected_llm_provider()
        
        # If no model specified, return default
        if not model:
            return self.get_default_model(provider)
        
        # Get available models for the provider
        if provider == SelectedLLMProvider.OPENAI:
            available_models = await self.get_available_openai_models()
            if model not in available_models:
                # Check if it's a valid model pattern even if not in list
                if not any(model.startswith(prefix) for prefix in ['gpt-4', 'gpt-3.5']):
                    raise ValueError(
                        f"Invalid OpenAI model '{model}'. Available models: {sorted(available_models)}"
                    )
        
        elif provider == SelectedLLMProvider.GOOGLE:
            available_models = await self.get_available_google_models()
            if model not in available_models:
                # Check if it's a valid model pattern
                if not any(model.startswith(prefix) for prefix in ['gemini']):
                    raise ValueError(
                        f"Invalid Google model '{model}'. Available models: {sorted(available_models)}"
                    )
        
        return model
    
    def get_default_model(self, provider: SelectedLLMProvider) -> str:
        """Get default model for a provider"""
        defaults = {
            SelectedLLMProvider.OPENAI: "gpt-4o",
            SelectedLLMProvider.GOOGLE: "gemini-2.0-flash",
            SelectedLLMProvider.OLLAMA: os.getenv("OLLAMA_MODEL", "llama3"),
            SelectedLLMProvider.CUSTOM: os.getenv("CUSTOM_MODEL", "")
        }
        return defaults.get(provider, "gpt-4o")
    
    def get_model_for_task(self, task: str, model: Optional[str] = None) -> str:
        """Get appropriate model for a specific task"""
        provider = get_selected_llm_provider()
        
        # If model specified, use it
        if model:
            return model
        
        # Task-based model selection
        task_models = {
            "large": {
                SelectedLLMProvider.OPENAI: "gpt-4o",
                SelectedLLMProvider.GOOGLE: "gemini-1.5-pro",
            },
            "small": {
                SelectedLLMProvider.OPENAI: "gpt-4o-mini",
                SelectedLLMProvider.GOOGLE: "gemini-1.5-flash",
            },
            "nano": {
                SelectedLLMProvider.OPENAI: "gpt-4o-mini",
                SelectedLLMProvider.GOOGLE: "gemini-1.5-flash",
            }
        }
        
        return task_models.get(task, {}).get(provider, self.get_default_model(provider))


# Global instance
model_manager_v2 = ModelManagerV2()