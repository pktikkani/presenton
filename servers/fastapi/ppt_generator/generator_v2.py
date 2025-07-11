"""Enhanced generator for V2 with slide mode support"""
import os
from typing import Optional

from ppt_generator.generator import (
    generate_presentation as generate_presentation_v1,
    generate_presentation_stream as generate_presentation_stream_v1,
    get_system_prompt,
    get_response_format,
    CREATE_PRESENTATION_PROMPT
)
from ppt_config_generator.models import PresentationMarkdownModel
from ppt_generator.slide_mode_config_v2 import (
    get_slide_mode_prompt_v2,
    get_system_prompt_for_mode,
    SLIDE_MODE_LIMITS_V2
)
from api.utils.model_utils_v2 import model_manager_v2
from api.utils.model_utils import get_llm_client


def get_system_prompt_v2() -> str:
    """Get enhanced system prompt with slide mode instructions"""
    slide_mode = os.environ.get("V2_SLIDE_MODE", "normal")
    mode_prompt = get_slide_mode_prompt_v2(slide_mode)
    system_prompt = get_system_prompt_for_mode(slide_mode)
    
    # Get the base prompt
    base_prompt = get_system_prompt()
    
    # Inject mode-specific instructions
    enhanced_prompt = f"""
{system_prompt}

{mode_prompt}

{base_prompt}

# IMPORTANT MODE-SPECIFIC LIMITS FOR {slide_mode.upper()} MODE:
"""
    
    # Add specific limits based on mode
    limits = SLIDE_MODE_LIMITS_V2.get(slide_mode, SLIDE_MODE_LIMITS_V2["normal"])
    
    enhanced_prompt += f"""
- Title: {limits['title']['min']}-{limits['title']['max']} characters
- Body/Description: {limits['body']['min']}-{limits['body']['max']} characters  
- List item descriptions: {limits['item_description']['min']}-{limits['item_description']['max']} characters
- Maximum items per list: {limits['max_items']}
- Target: {limits['word_count_guide']}

STRICTLY ADHERE TO THESE LIMITS!
"""
    
    return enhanced_prompt


async def generate_presentation_v2(
    presentation_outline: PresentationMarkdownModel,
) -> str:
    """Generate presentation with V2 enhancements"""
    client = get_llm_client()
    
    # Get model from V2 config or use default
    model_override = os.environ.get("V2_MODEL_OVERRIDE")
    if model_override:
        model = model_override
    else:
        # Use appropriate model based on slide mode
        slide_mode = os.environ.get("V2_SLIDE_MODE", "normal")
        task_type = "large" if slide_mode == "detailed" else "small"
        model = model_manager_v2.get_model_for_task(task_type)
    
    response_format = get_response_format()
    
    # Add mode information to the outline
    slide_mode = os.environ.get("V2_SLIDE_MODE", "normal")
    enhanced_outline = f"GENERATE IN {slide_mode.upper()} MODE\n\n{presentation_outline.to_string()}"
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": get_system_prompt_v2(),
            },
            {
                "role": "user",
                "content": enhanced_outline,
            },
        ],
        response_format=response_format,
        temperature=0.7,
    )
    
    return response.choices[0].message.content


async def generate_presentation_stream_v2(presentation_outline: PresentationMarkdownModel):
    """Stream generation with V2 enhancements"""
    client = get_llm_client()
    
    # Get model from V2 config
    model_override = os.environ.get("V2_MODEL_OVERRIDE")
    if model_override:
        model = model_override
    else:
        slide_mode = os.environ.get("V2_SLIDE_MODE", "normal")
        task_type = "large" if slide_mode == "detailed" else "small"
        model = model_manager_v2.get_model_for_task(task_type)
    
    response_format = get_response_format()
    
    # Add mode information
    slide_mode = os.environ.get("V2_SLIDE_MODE", "normal")
    enhanced_outline = f"GENERATE IN {slide_mode.upper()} MODE\n\n{presentation_outline.to_string()}"
    
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": get_system_prompt_v2(),
            },
            {
                "role": "user",
                "content": enhanced_outline,
            },
        ],
        response_format=response_format,
        stream=True,
        temperature=0.7,
    )
    
    return response