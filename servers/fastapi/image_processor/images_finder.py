import asyncio
import os
import uuid
import aiohttp
from google import genai
from google.genai.types import GenerateContentConfig

from ppt_generator.models.query_and_prompt_models import (
    ImagePromptWithThemeAndAspectRatio,
)
from api.utils.utils import download_file, get_resource
from api.utils.model_utils import (
    get_llm_client,
    is_custom_llm_selected,
    is_ollama_selected,
)


async def generate_image(
    input: ImagePromptWithThemeAndAspectRatio,
    output_directory: str,
    image_provider: str = None,
) -> str:
    is_ollama = is_ollama_selected()
    is_custom_llm = is_custom_llm_selected()

    image_prompt = (
        input.image_prompt
        if is_ollama or is_custom_llm
        else f"{input.image_prompt}, {input.theme_prompt}"
    )
    print(f"Request - Generating Image for {image_prompt}")

    try:
        # Use image_provider if specified, otherwise use default logic
        if image_provider:
            if image_provider.startswith("flux"):
                # Handle flux models - format: "flux:model-name" or just "flux" for default
                flux_model = "flux-kontext-pro"
                if ":" in image_provider:
                    flux_model = image_provider.split(":", 1)[1]
                aspect_ratio_str = input.aspect_ratio.value if input.aspect_ratio else "1:1"
                image_gen_func = lambda p, d: generate_image_flux(p, d, aspect_ratio_str, flux_model)
            elif image_provider == "openai":
                image_gen_func = generate_image_openai
            elif image_provider == "google":
                image_gen_func = generate_image_google
            elif image_provider == "pexels":
                image_gen_func = get_image_from_pexels
            else:
                raise Exception(f"Unknown image provider: {image_provider}")
        else:
            # Default to Flux for your use case
            aspect_ratio_str = input.aspect_ratio.value if input.aspect_ratio else "1:1"
            image_gen_func = lambda p, d: generate_image_flux(p, d, aspect_ratio_str, "flux-kontext-pro")
        
        image_path = await image_gen_func(image_prompt, output_directory)
        if image_path and os.path.exists(image_path):
            return image_path
        raise Exception(f"Image not found at {image_path}")

    except Exception as e:
        print(f"Error generating image: {e}")
        return get_resource("assets/images/placeholder.jpg")


async def generate_image_openai(prompt: str, output_directory: str) -> str:
    client = get_llm_client()
    result = await asyncio.to_thread(
        client.images.generate,
        model="dall-e-3",
        prompt=prompt,
        n=1,
        quality="standard",
        size="1024x1024",
    )
    image_url = result.data[0].url
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_bytes = await response.read()
            image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            return image_path


async def generate_image_google(prompt: str, output_directory: str) -> str:
    client = genai.Client()
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash-preview-image-generation",
        contents=[prompt],
        config=GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
            with open(image_path, "wb") as f:
                f.write(part.inline_data.data)

    return image_path


async def get_image_from_pexels(prompt: str, output_directory: str) -> str:
    async with aiohttp.ClientSession() as session:
        response = await session.get(
            f"https://api.pexels.com/v1/search?query={prompt}&per_page=1",
            headers={"Authorization": f'{os.getenv("PEXELS_API_KEY")}'},
        )
        data = await response.json()
        image_url = data["photos"][0]["src"]["large"]
        image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
        await download_file(image_url, image_path)
        return image_path


async def generate_image_flux(prompt: str, output_directory: str, aspect_ratio: str = "1:1", model: str = "flux-kontext-pro") -> str:
    """Generate images using Black Forest Labs Flux API
    
    Available models:
    - flux-kontext-max: $0.08/image - Maximum performance, improved prompt adherence and typography
    - flux-kontext-pro: $0.04/image - Unified model for editing and generation
    - flux-pro-1.1-ultra: $0.06/image - Best for photo-realistic images at 2k resolution
    - flux-pro-1.1: $0.04/image - Best and most efficient for large-scale generation
    - flux-pro: $0.05/image - Original pro model
    - flux-dev: $0.025/image - Distilled model
    """
    bfl_api_key = os.getenv("BFL_API_KEY")
    if not bfl_api_key:
        raise Exception("BFL_API_KEY not found in environment variables")
    
    # Map model names to endpoints
    model_endpoints = {
        "flux-kontext-max": "/v1/flux-kontext-max",
        "flux-kontext-pro": "/v1/flux-kontext-pro",
        "flux-pro-1.1-ultra": "/v1/flux-pro-1.1-ultra",
        "flux-pro-1.1": "/v1/flux-pro-1.1",
        "flux-pro": "/v1/flux-pro",
        "flux-dev": "/v1/flux-dev"
    }
    
    endpoint = model_endpoints.get(model, "/v1/flux-kontext-pro")
    
    async with aiohttp.ClientSession() as session:
        # Prepare request payload
        payload = {
            'prompt': prompt,
            'aspect_ratio': aspect_ratio
        }
        
        # Add raw option for ultra model
        if model == "flux-pro-1.1-ultra":
            payload['output_format'] = 'jpeg'  # Can be 'jpeg' or 'png'
            # payload['raw'] = True  # Uncomment for extra realism
        
        # Start generation request
        response = await session.post(
            f'https://api.bfl.ai{endpoint}',
            headers={
                'accept': 'application/json',
                'x-key': bfl_api_key,
                'Content-Type': 'application/json',
            },
            json=payload
        )
        
        if response.status != 200:
            raise Exception(f"Failed to generate image: {await response.text()}")
        
        result = await response.json()
        request_id = result.get("id")
        polling_url = result.get("polling_url")
        
        # Poll for completion
        max_attempts = 60  # 5 minutes max wait
        for _ in range(max_attempts):
            await asyncio.sleep(5)  # Wait 5 seconds between polls
            
            poll_response = await session.get(
                polling_url,
                headers={
                    'accept': 'application/json',
                    'x-key': bfl_api_key,
                }
            )
            
            if poll_response.status == 200:
                poll_data = await poll_response.json()
                status = poll_data.get("status")
                
                if status == "Ready":
                    image_url = poll_data.get("result", {}).get("sample")
                    if image_url:
                        image_path = os.path.join(output_directory, f"{str(uuid.uuid4())}.jpg")
                        await download_file(image_url, image_path)
                        return image_path
                    else:
                        raise Exception("No image URL in response")
                elif status == "Failed":
                    raise Exception(f"Image generation failed: {poll_data.get('error', 'Unknown error')}")
        
        raise Exception("Image generation timed out")
