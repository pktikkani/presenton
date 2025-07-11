import asyncio
import os
import uuid
import aiohttp
import time
from typing import Optional, Literal
from enum import Enum

from ppt_generator.models.query_and_prompt_models import (
    ImagePromptWithThemeAndAspectRatio,
)
from api.utils.utils import download_file, get_resource


class FluxModel(Enum):
    KONTEXT_MAX = ("flux-kontext-max", 0.08)
    KONTEXT_PRO = ("flux-kontext-pro", 0.04)
    PRO_1_1_ULTRA = ("flux-pro-1.1-ultra", 0.06)
    PRO_1_1 = ("flux-pro-1.1", 0.04)
    PRO = ("flux-pro", 0.05)
    DEV = ("flux-dev", 0.025)
    
    def __init__(self, endpoint: str, price: float):
        self.endpoint = endpoint
        self.price = price


async def generate_image(
    input: ImagePromptWithThemeAndAspectRatio,
    output_directory: str,
) -> str:
    # Combine image prompt with theme prompt for better results
    image_prompt = f"{input.image_prompt}, {input.theme_prompt}"
    print(f"Request - Generating Image for {image_prompt}")

    try:
        # Always use FLUX for image generation
        image_path = await generate_image_flux(image_prompt, output_directory)
        if image_path and os.path.exists(image_path):
            return image_path
        raise Exception(f"Image not found at {image_path}")

    except Exception as e:
        print(f"Error generating image: {e}")
        return get_resource("assets/images/placeholder.jpg")


async def generate_image_flux(
    prompt: str, 
    output_directory: str,
    model: FluxModel = None
) -> str:
    """Generate image using FLUX API"""
    # Use the model specified in environment or default to DEV
    if model is None:
        model_name = os.getenv("FLUX_MODEL", "DEV")
        model = FluxModel[model_name] if hasattr(FluxModel, model_name) else FluxModel.DEV
    
    api_key = os.getenv("BFL_API_KEY")
    if not api_key:
        raise Exception("BFL_API_KEY environment variable is not set")
    
    print(f"Using FLUX model: {model.name} (${model.price}/image)")
    
    # Make the initial request to FLUX API
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f'https://api.bfl.ai/v1/{model.endpoint}',
            headers={
                'accept': 'application/json',
                'x-key': api_key,
                'Content-Type': 'application/json',
            },
            json={
                'prompt': prompt,
                # Add raw mode for ultra model if needed
                'raw': model == FluxModel.PRO_1_1_ULTRA and os.getenv("FLUX_RAW_MODE", "false").lower() == "true"
            }
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"FLUX API error: {response.status} - {error_text}")
            
            data = await response.json()
            request_id = data.get("id")
            polling_url = data.get("polling_url")
            
            if not polling_url:
                raise Exception("No polling URL received from FLUX API")
        
        # Poll for the result
        max_attempts = 60  # 60 attempts with 2 second delays = 2 minutes max
        for attempt in range(max_attempts):
            await asyncio.sleep(2)  # Wait 2 seconds between polls
            
            async with session.get(
                polling_url,
                headers={
                    'accept': 'application/json',
                    'x-key': api_key,
                },
                params={'id': request_id}
            ) as poll_response:
                if poll_response.status != 200:
                    continue
                    
                poll_data = await poll_response.json()
                
                if poll_data.get("status") == "Ready":
                    # According to FLUX docs, the image URL is at result.sample
                    result = poll_data.get("result", {})
                    image_url = result.get("sample")
                    
                    if image_url:
                        # Download the image
                        async with session.get(image_url) as image_response:
                            if image_response.status == 200:
                                image_bytes = await image_response.read()
                                image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
                                with open(image_path, "wb") as f:
                                    f.write(image_bytes)
                                print(f"Image saved to: {image_path}")
                                return image_path
                            else:
                                raise Exception(f"Failed to download image from FLUX: HTTP {image_response.status}")
                    else:
                        print(f"FLUX response structure: {poll_data}")
                        raise Exception("No image URL in FLUX response")
                
                elif poll_data.get("status") == "Error":
                    error_msg = poll_data.get("error", "Unknown error")
                    raise Exception(f"FLUX generation error: {error_msg}")
        
        raise Exception("FLUX image generation timed out after 2 minutes")
