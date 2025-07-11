"""PydanticAI Agents with output validators for V2"""
from typing import Optional, Dict, Any
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelRetry

from .models import Presentation, Slide, SlideContent, FlexibleListItem
from .model_manager import model_manager
from ppt_generator.slide_mode_config import get_slide_mode_prompt


def validate_and_fix_slide_content(ctx: RunContext, slide: Slide) -> Slide:
    """Validate and fix common slide content issues"""
    content = slide.content
    slide_type = slide.type
    
    # Type 1: Title + Body (string) + Image
    if slide_type == 1:
        if not isinstance(content.body, str):
            if isinstance(content.body, list):
                # Convert list to string
                items_text = "\n".join([
                    f"• {item.heading or item.title}: {item.description}"
                    for item in content.body
                ])
                raise ModelRetry(
                    f"Type 1 slides need body as text, not a list. "
                    f"Convert this list to paragraph text: {items_text}"
                )
            else:
                content.body = str(content.body) if content.body else ""
        
        if not content.body or len(content.body.strip()) < 10:
            raise ModelRetry(
                f"Type 1 slides need meaningful body text. "
                f"Expand on '{content.title}' with at least 2-3 sentences."
            )
        
        if not content.image_prompt:
            content.image_prompt = f"professional presentation visual for {content.title}"
    
    # Types with lists: 2, 3, 4, 6, 7, 8
    elif slide_type in [2, 3, 4, 6, 7, 8]:
        if not isinstance(content.body, list):
            if isinstance(content.body, str):
                raise ModelRetry(
                    f"Type {slide_type} slides need list items, not paragraph text. "
                    f"Convert this text to a list of items with headings and descriptions: {content.body}"
                )
            content.body = []
        
        if len(content.body) == 0:
            raise ModelRetry(
                f"Type {slide_type} slides must have at least 2-3 list items. "
                f"Add relevant points about '{content.title}'"
            )
        
        # Validate list items
        for i, item in enumerate(content.body):
            if not item.description or len(item.description.strip()) < 5:
                raise ModelRetry(
                    f"List item {i+1} needs a meaningful description. "
                    f"Expand on '{item.heading or item.title}'"
                )
            
            # Type-specific validations
            if slide_type == 4 and not item.image_prompt:
                item.image_prompt = f"visual for {item.heading or item.title}"
            elif slide_type == 7 and not item.icon_query:
                item.icon_query = item.heading or item.title or "icon"
            elif slide_type == 8 and not item.image_prompt:
                item.image_prompt = f"image for {item.heading or item.title}"
        
        # Additional fields for specific types
        if slide_type == 3 and not content.image_prompt:
            content.image_prompt = f"visual representation of {content.title}"
        
        if slide_type in [6, 8] and not content.description:
            raise ModelRetry(
                f"Type {slide_type} slides need a description field. "
                f"Add a brief overview paragraph about '{content.title}'"
            )
    
    # Type 5: Title + Body + Graph
    elif slide_type == 5:
        if not isinstance(content.body, str):
            content.body = str(content.body) if content.body else ""
        
        if not content.graph:
            raise ModelRetry(
                "Type 5 slides must have a graph. Add a graph with type (pie/bar/line), "
                "name, data with categories/labels and values."
            )
        
        if not content.graph.data or not content.graph.data.series:
            raise ModelRetry(
                "Graph needs proper data structure. Include 'type', 'name', and 'data' "
                "with 'categories' (labels) and 'series' (values)."
            )
    
    # Type 9: Title + Description + Table + Graph
    elif slide_type == 9:
        if not content.description:
            raise ModelRetry(
                f"Type 9 slides need a description. "
                f"Add an overview paragraph about '{content.title}'"
            )
        
        if not isinstance(content.body, list):
            content.body = []
        
        if not content.graph:
            raise ModelRetry(
                "Type 9 slides must have both table data (in body) and a graph."
            )
    
    return slide


def validate_presentation_output(ctx: RunContext, presentation: Presentation) -> Presentation:
    """Main output validator for presentations"""
    
    # Validate title
    if not presentation.title or len(presentation.title.strip()) < 3:
        raise ModelRetry("Presentation needs a meaningful title (at least 3 characters)")
    
    # Validate slides exist
    if not presentation.slides or len(presentation.slides) == 0:
        raise ModelRetry("Presentation must have at least one slide")
    
    # Validate each slide
    for i, slide in enumerate(presentation.slides):
        try:
            presentation.slides[i] = validate_and_fix_slide_content(ctx, slide)
        except ModelRetry:
            raise  # Re-raise ModelRetry exceptions
        except Exception as e:
            raise ModelRetry(f"Error in slide {i+1}: {str(e)}")
    
    return presentation


def create_presentation_agent(
    model_string: str,
    slide_mode: str = "normal",
    max_retries: int = 3
) -> Agent[str, Presentation]:
    """Create a PydanticAI agent for presentation generation"""
    
    # Get mode-specific instructions
    mode_prompt = get_slide_mode_prompt(slide_mode)
    
    system_prompt = f"""
You are an expert presentation creator. Generate professional presentations with engaging content.

# Slide Types:
1. Type 1: Title + Body (paragraph text) + Image prompt
2. Type 2: Title + List items (bullet points)
3. Type 3: Title + List items + Image prompt
4. Type 4: Title + List items with individual images
5. Type 5: Title + Body text + Graph
6. Type 6: Title + Description + List items
7. Type 7: Title + List items with icons
8. Type 8: Title + Description + List items with images
9. Type 9: Title + Description + Table data + Graph

# Important Instructions:
- Use appropriate slide types for the content
- For list items, you can use either "heading" or "title" field
- Ensure all text is meaningful and relevant
- Include variety in slide types throughout the presentation
- Generate engaging image prompts without text/numbers
- For graphs, specify type (pie/bar/line) and provide proper data structure

# Content Mode: {slide_mode}
{mode_prompt}

# Common Corrections from Previous Attempts:
- Type 1 needs body as string, not list
- Types 2,3,4,6,7,8 need body as list of items
- Type 6 and 8 need description field
- Type 5 and 9 need graph data
- List items need meaningful descriptions
"""
    
    # Create agent
    agent = Agent(
        model=model_string,
        output_type=Presentation,
        system_prompt=system_prompt,
        retries=max_retries,
    )
    
    # Add output validator
    agent.output_validator(validate_presentation_output)
    
    return agent