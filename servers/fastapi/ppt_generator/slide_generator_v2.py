"""Enhanced slide generator for V2 with better mode differentiation"""
import os
from typing import Optional

from ppt_generator.slide_generator import SlideGenerator
from ppt_generator.slide_mode_config_v2 import (
    get_slide_mode_prompt_v2,
    get_content_guidelines_v2,
    get_system_prompt_for_mode,
    SLIDE_MODE_LIMITS_V2
)
from api.utils.model_utils_v2 import model_manager_v2
from api.utils.model_utils import get_llm_client


class SlideGeneratorV2(SlideGenerator):
    """Enhanced slide generator with V2 features"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get V2 configuration from environment
        self.slide_mode = os.environ.get("V2_SLIDE_MODE", "normal")
        self.model_override = os.environ.get("V2_MODEL_OVERRIDE")
        
        # Update prompts based on V2 mode
        self._update_prompts_for_mode()
    
    def _update_prompts_for_mode(self):
        """Update generation prompts based on slide mode"""
        mode_prompt = get_slide_mode_prompt_v2(self.slide_mode)
        system_prompt = get_system_prompt_for_mode(self.slide_mode)
        
        # Prepend mode instructions to existing prompts
        self.system_prompt = f"{system_prompt}\n\n{mode_prompt}\n\n{self.system_prompt}"
    
    async def _generate_with_model(self, prompt: str, slide_type: int) -> dict:
        """Generate content with specific model and mode constraints"""
        # Get content guidelines for this mode and slide type
        guidelines = get_content_guidelines_v2(self.slide_mode, slide_type)
        
        # Add guidelines to prompt
        enhanced_prompt = f"""
{prompt}

IMPORTANT CONTENT LIMITS FOR {self.slide_mode.upper()} MODE:
- Title: {guidelines['title']['min']}-{guidelines['title']['max']} characters
- Body text: {guidelines['body']['min']}-{guidelines['body']['max']} characters
- List items: Maximum {guidelines['max_items']} items
- Item descriptions: {guidelines['item_description']['min']}-{guidelines['item_description']['max']} characters each
- Overall: {guidelines['word_count_guide']}
"""
        
        # Get appropriate model
        if self.model_override:
            model = self.model_override
        else:
            # Use different models based on mode for cost optimization
            task_type = {
                "compact": "small",  # Use smaller model for compact content
                "normal": "small",   # Normal can use small model
                "detailed": "large"  # Detailed needs larger model
            }.get(self.slide_mode, "small")
            
            model = model_manager_v2.get_model_for_task(task_type)
        
        # Generate content
        client = get_llm_client()
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.7,
            max_tokens=self._get_max_tokens_for_mode()
        )
        
        return response.choices[0].message.content
    
    def _get_max_tokens_for_mode(self) -> int:
        """Get appropriate max tokens based on mode"""
        max_tokens = {
            "compact": 500,
            "normal": 1000,
            "detailed": 2000
        }
        return max_tokens.get(self.slide_mode, 1000)
    
    def _validate_content_length(self, content: dict, slide_type: int) -> dict:
        """Validate and adjust content based on mode limits"""
        guidelines = get_content_guidelines_v2(self.slide_mode, slide_type)
        
        # Validate title
        if 'title' in content:
            if len(content['title']) > guidelines['title']['max']:
                content['title'] = content['title'][:guidelines['title']['max']-3] + "..."
        
        # Validate body
        if 'body' in content:
            if isinstance(content['body'], str) and len(content['body']) > guidelines['body']['max']:
                content['body'] = content['body'][:guidelines['body']['max']-3] + "..."
        
        # Validate list items
        if 'items' in content and isinstance(content['items'], list):
            # Limit number of items
            content['items'] = content['items'][:guidelines['max_items']]
            
            # Validate each item
            for item in content['items']:
                if 'description' in item and len(item['description']) > guidelines['item_description']['max']:
                    item['description'] = item['description'][:guidelines['item_description']['max']-3] + "..."
        
        return content