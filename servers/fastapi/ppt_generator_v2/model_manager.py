"""Model validation and management for V2"""
import os
from typing import Optional, List, Set, Dict
from functools import lru_cache
import httpx

from api.models import SelectedLLMProvider
from api.utils.model_utils import get_llm_api_key, get_selected_llm_provider


class ModelManager:
    """Manages LLM model validation and selection"""
    
    def __init__(self):
        self._available_models_cache: Dict[str, Set[str]] = {}
        
    async def get_available_openai_models(self) -> Set[str]:
        """Get list of available OpenAI models"""
        if "openai" in self._available_models_cache:
            return self._available_models_cache["openai"]
            
        api_key = get_llm_api_key()
        if not api_key:
            return set()
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                if response.status_code == 200:
                    models = response.json()["data"]
                    model_ids = {m["id"] for m in models}
                    self._available_models_cache["openai"] = model_ids
                    return model_ids
        except Exception as e:
            print(f"Error fetching OpenAI models: {e}")
            
        # Fallback to known models
        return {
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", 
            "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
        }
    
    async def get_available_gemini_models(self) -> Set[str]:
        """Get list of available Gemini models"""
        if "gemini" in self._available_models_cache:
            return self._available_models_cache["gemini"]
            
        api_key = get_llm_api_key()
        if not api_key:
            return set()
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
                )
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = {m["name"].replace("models/", "") for m in models}
                    self._available_models_cache["gemini"] = model_names
                    return model_names
        except Exception as e:
            print(f"Error fetching Gemini models: {e}")
            
        # Fallback to known models
        return {
            "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", 
            "gemini-pro-vision", "gemini-1.5-pro-latest"
        }
    
    async def validate_model(self, model: Optional[str] = None) -> str:
        """Validate and return model string for PydanticAI"""
        provider = get_selected_llm_provider()
        
        if not model:
            # Use defaults
            if provider == SelectedLLMProvider.OPENAI:
                return "openai:gpt-4o"
            elif provider == SelectedLLMProvider.GOOGLE:
                return "gemini-1.5-pro"
            else:
                raise ValueError(f"Unsupported provider: {provider}")
        
        # Validate model exists
        if provider == SelectedLLMProvider.OPENAI:
            available = await self.get_available_openai_models()
            if model not in available:
                raise ValueError(
                    f"Model '{model}' not available. Available models: {sorted(available)}"
                )
            return f"openai:{model}"
            
        elif provider == SelectedLLMProvider.GOOGLE:
            available = await self.get_available_gemini_models()
            if model not in available:
                raise ValueError(
                    f"Model '{model}' not available. Available models: {sorted(available)}"
                )
            # Gemini models in PydanticAI don't use prefix
            return model
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def setup_api_keys(self):
        """Setup API keys in environment"""
        provider = get_selected_llm_provider()
        api_key = get_llm_api_key()
        
        if not api_key:
            raise ValueError(f"API key not found for provider: {provider}")
            
        if provider == SelectedLLMProvider.OPENAI:
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == SelectedLLMProvider.GOOGLE:
            os.environ["GEMINI_API_KEY"] = api_key


# Global instance
model_manager = ModelManager()