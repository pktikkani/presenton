"""Main presentation generator for V2"""
import json
from typing import Optional, Dict, Any
from pydantic_ai.exceptions import UnexpectedModelBehavior

from .models import Presentation, PresentationResponse
from .agents import create_presentation_agent
from .model_manager import model_manager
from ppt_config_generator.models import PresentationMarkdownModel


def convert_to_api_format(presentation: Presentation) -> Dict[str, Any]:
    """Convert Presentation model to API format matching V1 structure"""
    slides = []
    
    for slide in presentation.slides:
        slide_dict = {
            "type": slide.type,
            "notes": slide.notes or ""
        }
        
        content = slide.content
        content_dict = {"title": content.title}
        
        # Convert based on slide type
        if slide.type == 1:
            content_dict["body"] = content.body if isinstance(content.body, str) else ""
            content_dict["image_prompt"] = content.image_prompt or ""
            
        elif slide.type in [2, 3, 4, 6, 7, 8]:
            # Convert FlexibleListItem to dict format
            items = []
            if isinstance(content.body, list):
                for item in content.body:
                    item_dict = {
                        "heading": item.heading or item.title or "",
                        "description": item.description
                    }
                    
                    if slide.type == 4:
                        item_dict["image_prompt"] = item.image_prompt or ""
                    elif slide.type == 7:
                        item_dict["icon_query"] = item.icon_query or "icon"
                    elif slide.type == 8:
                        item_dict["image_prompt"] = item.image_prompt or ""
                        
                    items.append(item_dict)
            
            content_dict["body"] = items
            
            if slide.type == 3:
                content_dict["image_prompt"] = content.image_prompt or ""
            elif slide.type in [6, 8]:
                content_dict["description"] = content.description or ""
                
        elif slide.type == 5:
            content_dict["body"] = content.body if isinstance(content.body, str) else ""
            if content.graph:
                graph_dict = {
                    "type": content.graph.type.value,
                    "name": content.graph.name,
                    "unit": content.graph.unit,
                    "x_axis": content.graph.x_axis,
                    "y_axis": content.graph.y_axis,
                }
                if content.graph.data and content.graph.data.series:
                    graph_dict["series"] = content.graph.data.series
                content_dict["graph"] = graph_dict
            else:
                content_dict["graph"] = {"x_axis": "X", "y_axis": "Y", "series": []}
                
        elif slide.type == 9:
            content_dict["description"] = content.description or ""
            content_dict["body"] = []
            if isinstance(content.body, list):
                for item in content.body:
                    content_dict["body"].append({
                        "heading": item.heading or item.title or "",
                        "description": item.description
                    })
            
            if content.graph:
                graph_dict = {
                    "type": content.graph.type.value,
                    "name": content.graph.name,
                    "unit": content.graph.unit,
                    "x_axis": content.graph.x_axis,
                    "y_axis": content.graph.y_axis,
                }
                if content.graph.data and content.graph.data.series:
                    graph_dict["series"] = content.graph.data.series
                content_dict["graph"] = graph_dict
            else:
                content_dict["graph"] = {"x_axis": "X", "y_axis": "Y", "series": []}
        
        slide_dict["content"] = content_dict
        slides.append(slide_dict)
    
    return {
        "title": presentation.title,
        "slides": slides
    }


async def generate_presentation_v2(
    presentation_outline: PresentationMarkdownModel,
    slide_mode: str = "normal",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate presentation using PydanticAI with advanced error handling"""
    
    try:
        # Validate and setup model
        model_string = await model_manager.validate_model(model)
        model_manager.setup_api_keys()
        
        # Create agent
        agent = create_presentation_agent(model_string, slide_mode)
        
        # Generate presentation
        result = await agent.run(presentation_outline.to_string())
        
        # Convert to API format
        api_format = convert_to_api_format(result.output)
        
        # Log token usage if available
        if result.usage:
            print(f"Token usage - Input: {result.usage.input_tokens}, "
                  f"Output: {result.usage.output_tokens}, "
                  f"Total: {result.usage.total_tokens}")
        
        return api_format
        
    except UnexpectedModelBehavior as e:
        # This happens when retries are exhausted
        error_details = []
        if hasattr(e, 'last_error'):
            error_details.append(str(e.last_error))
        
        raise ValueError(
            f"Failed to generate valid presentation after retries. "
            f"Last error: {error_details}"
        )
    
    except Exception as e:
        raise ValueError(f"Presentation generation failed: {str(e)}")


async def generate_presentation_stream_v2(
    presentation_outline: PresentationMarkdownModel,
    slide_mode: str = "normal",
    model: Optional[str] = None,
):
    """Generate presentation with streaming support"""
    # For now, generate complete and simulate streaming
    # PydanticAI doesn't support streaming with structured output yet
    
    try:
        result = await generate_presentation_v2(
            presentation_outline, slide_mode, model
        )
        
        # Convert to JSON and stream in chunks
        json_str = json.dumps(result)
        chunk_size = 100
        
        for i in range(0, len(json_str), chunk_size):
            chunk = json_str[i:i+chunk_size]
            yield f"data: {json.dumps({'chunk': chunk, 'type': 'chunk'})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"