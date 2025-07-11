import json
import os
from typing import AsyncGenerator, Optional

import aiohttp
from fastapi import HTTPException
from openai import AsyncOpenAI
import openai

from api.models import SelectedLLMProvider






def get_selected_llm_provider() -> SelectedLLMProvider:
    provider = os.getenv("LLM", "openai").lower()
    if provider in ["google", "gemini"]:
        return SelectedLLMProvider.GOOGLE
    else:
        # Default to OpenAI
        return SelectedLLMProvider.OPENAI




def get_model_base_url():
    selected_llm = get_selected_llm_provider()

    if selected_llm == SelectedLLMProvider.OPENAI:
        return "https://api.openai.com/v1"
    elif selected_llm == SelectedLLMProvider.GOOGLE:
        return "https://generativelanguage.googleapis.com/v1beta/openai"
    else:
        raise ValueError(f"Invalid LLM provider")


def get_llm_api_key():
    selected_llm = get_selected_llm_provider()
    if selected_llm == SelectedLLMProvider.OPENAI:
        return os.getenv("OPENAI_API_KEY")
    elif selected_llm == SelectedLLMProvider.GOOGLE:
        return os.getenv("GOOGLE_API_KEY")
    else:
        raise ValueError(f"Invalid LLM API key")


def get_llm_client():
    client = AsyncOpenAI(
        base_url=get_model_base_url(),
        api_key=get_llm_api_key(),
    )
    return client


def get_large_model():
    selected_llm = get_selected_llm_provider()
    if selected_llm == SelectedLLMProvider.OPENAI:
        return "gpt-4o"
    elif selected_llm == SelectedLLMProvider.GOOGLE:
        return "gemini-1.5-pro"
    else:
        raise ValueError(f"Invalid LLM model")


def get_small_model():
    selected_llm = get_selected_llm_provider()
    if selected_llm == SelectedLLMProvider.OPENAI:
        return "gpt-4o-mini"
    elif selected_llm == SelectedLLMProvider.GOOGLE:
        return "gemini-1.5-flash"
    else:
        raise ValueError(f"Invalid LLM model")


def get_nano_model():
    selected_llm = get_selected_llm_provider()
    if selected_llm == SelectedLLMProvider.OPENAI:
        return "gpt-4o-mini"  # Use mini for nano as well
    elif selected_llm == SelectedLLMProvider.GOOGLE:
        return "gemini-1.5-flash"
    else:
        raise ValueError(f"Invalid LLM model")


