"""Enhanced image finder for V2 with Flux model selection"""
import asyncio
import os
import uuid
import aiohttp
from enum import Enum
from typing import Optional

from ppt_generator.models.query_and_prompt_models import ImagePromptWithThemeAndAspectRatio
from api.utils.utils import download_file, get_resource
from api.utils.model_utils import get_llm_client
from api.routers.v2.models import ImageProvider, FluxModel as FluxModelEnum


class FluxModelConfig(Enum):
    """Flux model configurations with pricing"""
    KONTEXT_MAX = ("kontext-max", "flux-kontext-max", 0.08)
    KONTEXT_PRO = ("kontext-pro", "flux-kontext-pro", 0.04)
    PRO_1_1_ULTRA = ("pro-1.1-ultra", "flux-pro-1.1-ultra", 0.06)
    PRO_1_1 = ("pro-1.1", "flux-pro-1.1", 0.04)
    PRO = ("pro", "flux-pro", 0.05)
    DEV = ("dev", "flux-dev", 0.025)
    
    def __init__(self, key: str, endpoint: str, price: float):
        self.key = key
        self.endpoint = endpoint
        self.price = price
    
    @classmethod
    def from_enum(cls, model_enum: FluxModelEnum) -> 'FluxModelConfig':
        """Convert from API enum to config"""
        mapping = {
            FluxModelEnum.KONTEXT_MAX: cls.KONTEXT_MAX,
            FluxModelEnum.KONTEXT_PRO: cls.KONTEXT_PRO,
            FluxModelEnum.PRO_1_1_ULTRA: cls.PRO_1_1_ULTRA,
            FluxModelEnum.PRO_1_1: cls.PRO_1_1,
            FluxModelEnum.PRO: cls.PRO,
            FluxModelEnum.DEV: cls.DEV,
        }
        return mapping.get(model_enum, cls.DEV)


async def generate_image_v2(
    input: ImagePromptWithThemeAndAspectRatio,
    output_directory: str,
    provider: Optional[ImageProvider] = None,
    flux_model: Optional[FluxModelEnum] = None,
) -> str:
    """Enhanced image generation with provider selection"""
    
    # Determine provider if not specified
    if provider is None:
        if os.getenv("BFL_API_KEY"):
            provider = ImageProvider.FLUX
        elif os.getenv("LLM") == "openai":
            provider = ImageProvider.OPENAI
        elif os.getenv("LLM") == "google":
            provider = ImageProvider.GOOGLE
        else:
            provider = ImageProvider.PEXELS
    
    # Prepare prompt based on provider
    if provider in [ImageProvider.PEXELS]:
        image_prompt = input.image_prompt
    else:
        image_prompt = f"{input.image_prompt}, {input.theme_prompt}"
    
    print(f"Generating image with {provider.value} for: {image_prompt}")
    
    try:
        if provider == ImageProvider.FLUX:
            return await generate_image_flux_v2(image_prompt, output_directory, flux_model)
        elif provider == ImageProvider.OPENAI:
            return await generate_image_openai_v2(image_prompt, output_directory)
        elif provider == ImageProvider.GOOGLE:
            return await generate_image_google_v2(image_prompt, output_directory)
        elif provider == ImageProvider.PEXELS:
            return await get_image_from_pexels(image_prompt, output_directory)
        else:
            raise ValueError(f"Unknown image provider: {provider}")
            
    except Exception as e:
        print(f"Error generating image with {provider.value}: {e}")
        # Fallback to placeholder
        return get_resource("assets/images/placeholder.jpg")


async def generate_image_flux_v2(
    prompt: str, 
    output_directory: str,
    model_enum: Optional[FluxModelEnum] = None
) -> str:
    """Enhanced Flux image generation with model selection"""
    
    # Get model configuration
    if model_enum is None:
        model_name = os.getenv("FLUX_MODEL", "DEV")
        try:
            model_enum = FluxModelEnum(model_name.lower())
        except ValueError:
            model_enum = FluxModelEnum.DEV
    
    model_config = FluxModelConfig.from_enum(model_enum)
    
    api_key = os.getenv("BFL_API_KEY")
    if not api_key:
        raise Exception("BFL_API_KEY environment variable is not set")
    
    print(f"Using FLUX model: {model_config.key} (${model_config.price}/image)")
    
    # Enhanced prompt for better quality
    enhanced_prompt = f"{prompt}, high quality, professional, sharp focus, detailed"
    
    async with aiohttp.ClientSession() as session:
        # Initial request with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                request_data = {
                    'prompt': enhanced_prompt,
                    'aspect_ratio': '1:1',  # Using aspect ratio as per BFL docs
                }
                
                # Add raw mode for ultra model if enabled
                if model_enum == FluxModelEnum.PRO_1_1_ULTRA:
                    if os.getenv("FLUX_RAW_MODE", "false").lower() == "true":
                        request_data['raw'] = True
                
                async with session.post(
                    f'https://api.bfl.ai/v1/{model_config.endpoint}',
                    headers={
                        'accept': 'application/json',
                        'x-key': api_key,
                        'Content-Type': 'application/json',
                    },
                    json=request_data
                ) as response:
                    if response.status == 429:
                        wait_time = 2 ** attempt
                        print(f"Rate limited, waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    elif response.status == 402:
                        raise Exception("Insufficient credits. Please add credits to your BFL account.")
                    
                    elif response.status == 403:
                        error_text = await response.text()
                        print(f"FLUX 403 error details: {error_text}")
                        raise Exception(f"FLUX API authentication error (403): {error_text}. Check your BFL_API_KEY.")
                    
                    elif response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"FLUX API error: {response.status} - {error_text}")
                    
                    data = await response.json()
                    request_id = data.get("id")
                    polling_url = data.get("polling_url")
                    
                    if not request_id or not polling_url:
                        raise Exception("No request ID or polling URL received from FLUX API")
                    
                    break
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)
        
        # Poll for result using the polling URL
        max_attempts = 90  # 3 minutes max
        for attempt in range(max_attempts):
            await asyncio.sleep(2)
            
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
                        raise Exception("No image URL in FLUX response")
                
                elif poll_data.get("status") in ["Error", "Failed"]:
                    error_msg = poll_data.get("error", "Unknown error")
                    raise Exception(f"FLUX generation error: {error_msg}")
        
        raise Exception("FLUX image generation timed out")


async def generate_image_openai_v2(prompt: str, output_directory: str) -> str:
    """OpenAI DALL-E 3 image generation"""
    client = get_llm_client()
    
    # You can make this configurable too
    quality = os.getenv("DALLE_QUALITY", "standard")  # "standard" or "hd"
    size = os.getenv("DALLE_SIZE", "1024x1024")  # "1024x1024", "1024x1792", "1792x1024"
    
    result = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        quality=quality,
        size=size,
    )
    
    image_url = result.data[0].url
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_bytes = await response.read()
            image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            return image_path


async def generate_image_google_v2(prompt: str, output_directory: str) -> str:
    """Google Imagen generation - using the existing implementation"""
    # Import the existing Google implementation
    from image_processor.images_finder import generate_image_google
    return await generate_image_google(prompt, output_directory)


async def get_image_from_pexels(prompt: str, output_directory: str) -> str:
    """Pexels image search"""
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise Exception("PEXELS_API_KEY not set")
    
    async with aiohttp.ClientSession() as session:
        response = await session.get(
            f"https://api.pexels.com/v1/search?query={prompt}&per_page=1&size=large",
            headers={"Authorization": api_key},
        )
        data = await response.json()
        
        if data.get("photos"):
            image_url = data["photos"][0]["src"]["large"]
            image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
            await download_file(image_url, image_path)
            return image_path
        else:
            raise Exception("No images found on Pexels")