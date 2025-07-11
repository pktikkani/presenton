"""Enhanced validators using PydanticAI for better content generation"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, ModelRetry, RunContext

from ppt_generator.models.slide_model import SlideModel
from ppt_generator.slide_mode_config_v2 import SLIDE_MODE_LIMITS_V2


class SlideContentValidator:
    """Validates and fixes slide content using PydanticAI"""
    
    def __init__(self, slide_mode: str = "normal"):
        self.slide_mode = slide_mode
        self.limits = SLIDE_MODE_LIMITS_V2.get(slide_mode, SLIDE_MODE_LIMITS_V2["normal"])
        
        # Create a PydanticAI agent for content validation
        self.agent = Agent(
            'openai:gpt-4o-mini',  # Use a small model for validation
            system_prompt="""You are a presentation content validator. 
            Your job is to ensure content meets specific length requirements while maintaining quality.
            When content is too long, summarize it. When too short, expand it with relevant details."""
        )
    
    async def validate_and_fix_slide(self, slide: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix slide content to meet mode requirements"""
        
        # Define a result model for the agent
        class ValidatedSlide(BaseModel):
            title: str = Field(..., min_length=self.limits['title']['min'], 
                               max_length=self.limits['title']['max'])
            content: Dict[str, Any]
        
        # Create validation prompt
        validation_prompt = f"""
        Validate and fix this slide content for {self.slide_mode} mode:
        
        Current slide: {slide}
        
        Requirements:
        - Title: {self.limits['title']['min']}-{self.limits['title']['max']} characters
        - Body/Description: {self.limits['body']['min']}-{self.limits['body']['max']} characters
        - List items: Maximum {self.limits['max_items']} items
        - Item descriptions: {self.limits['item_description']['min']}-{self.limits['item_description']['max']} characters
        
        Fix any content that doesn't meet these requirements.
        """
        
        @self.agent.result_validator
        def validate_slide_content(ctx: RunContext[Dict], result: ValidatedSlide) -> ValidatedSlide:
            """Validate the generated content meets requirements"""
            
            # Check title length
            if len(result.title) < self.limits['title']['min']:
                raise ModelRetry(f"Title too short. Expand to at least {self.limits['title']['min']} characters")
            if len(result.title) > self.limits['title']['max']:
                raise ModelRetry(f"Title too long. Shorten to at most {self.limits['title']['max']} characters")
            
            # Validate content based on slide type
            content = result.content
            if 'body' in content and isinstance(content['body'], str):
                if len(content['body']) < self.limits['body']['min']:
                    raise ModelRetry(f"Body text too short. Expand to at least {self.limits['body']['min']} characters")
                if len(content['body']) > self.limits['body']['max']:
                    raise ModelRetry(f"Body text too long. Shorten to at most {self.limits['body']['max']} characters")
            
            return result
        
        try:
            # Run the agent to validate and fix content
            result = await self.agent.run(validation_prompt, result_type=ValidatedSlide)
            return result.data.model_dump()
        except Exception as e:
            print(f"Validation error: {e}")
            # Return original slide if validation fails
            return slide


class PresentationValidator:
    """Validates entire presentations using PydanticAI"""
    
    def __init__(self, slide_mode: str = "normal"):
        self.slide_mode = slide_mode
        self.slide_validator = SlideContentValidator(slide_mode)
        
        # Agent for overall presentation coherence
        self.coherence_agent = Agent(
            'openai:gpt-4o-mini',
            system_prompt="""You are a presentation quality checker.
            Ensure presentations have logical flow and consistent style."""
        )
    
    async def validate_presentation(self, slides: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Validate and improve entire presentation"""
        
        # First, validate individual slides
        validated_slides = []
        for slide in slides:
            validated_slide = await self.slide_validator.validate_and_fix_slide(slide)
            validated_slides.append(validated_slide)
        
        # Then check overall coherence
        class PresentationFlow(BaseModel):
            has_good_flow: bool
            suggestions: list[str] = Field(default_factory=list)
        
        flow_check_prompt = f"""
        Check if this presentation has good flow and coherence:
        
        Slides: {[s['title'] for s in validated_slides]}
        
        Mode: {self.slide_mode}
        
        Return whether the flow is good and any suggestions for improvement.
        """
        
        try:
            flow_result = await self.coherence_agent.run(
                flow_check_prompt, 
                result_type=PresentationFlow
            )
            
            if not flow_result.data.has_good_flow:
                print(f"Flow suggestions: {flow_result.data.suggestions}")
        except Exception as e:
            print(f"Flow check error: {e}")
        
        return validated_slides


# Example usage function
async def enhance_slide_with_pydantic_ai(slide_data: Dict[str, Any], mode: str = "normal") -> Dict[str, Any]:
    """Enhance a single slide using PydanticAI validation"""
    validator = SlideContentValidator(mode)
    return await validator.validate_and_fix_slide(slide_data)