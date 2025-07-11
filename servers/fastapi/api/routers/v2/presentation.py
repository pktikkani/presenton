"""V2 Presentation API endpoints using PydanticAI"""
import uuid
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.models import ThemeNames
from api.services.database import get_sql_session
from api.sql_models import PresentationSqlModel, SlideSqlModel
from api.utils.utils import get_presentation_dir, handle_errors
from api.services.logging import LoggingService, get_log_metadata

from ppt_config_generator.models import PresentationMarkdownModel
from ppt_config_generator.ppt_outlines_generator import generate_ppt_content
from ppt_generator_v2.generator import generate_presentation_v2, generate_presentation_stream_v2
from ppt_generator.models.slide_model import SlideModel

# Import the asset fetching mixin from v1
from api.routers.presentation.mixins.fetch_assets_on_generation import (
    FetchAssetsOnPresentationGenerationMixin
)


router = APIRouter(prefix="/ppt", tags=["presentation-v2"])


class GeneratePresentationRequestV2(BaseModel):
    """V2 Request model with model validation"""
    prompt: Optional[str] = Field(None, description="Main prompt for presentation")
    n_slides: int = Field(5, ge=3, le=20, description="Number of slides")
    language: Optional[str] = Field("en", description="Language code")
    content: Optional[str] = Field(None, description="Additional content")
    theme: ThemeNames = Field(ThemeNames.YELLOW, description="Presentation theme")
    slide_mode: str = Field("normal", description="Slide mode: compact, normal, detailed")
    model: Optional[str] = Field(None, description="Specific model to use (e.g., gpt-4o, gemini-1.5-pro)")


class GeneratePresentationHandlerV2(FetchAssetsOnPresentationGenerationMixin):
    """V2 handler using PydanticAI"""
    
    def __init__(self, presentation_id: str, data: GeneratePresentationRequestV2):
        self.presentation_id = presentation_id
        self.data = data
        self.theme = {"name": data.theme.value, "colors": {}}
        self.session = str(uuid.uuid4())
    
    async def generate(self, logging_service: LoggingService, log_metadata: dict):
        """Generate presentation using V2 with PydanticAI"""
        
        # Log request
        logging_service.logger.info(
            f"V2 Presentation generation request: {self.data.model_dump()}",
            extra=log_metadata
        )
        
        # Generate outline first (using existing v1 function)
        print("-" * 40)
        print("V2: Generating PPT Outline")
        presentation_content = await generate_ppt_content(
            self.data.prompt,
            self.data.n_slides,
            self.data.language,
            self.data.content,
        )
        
        # Generate presentation with V2
        print("-" * 40)
        print("V2: Generating Presentation with PydanticAI")
        try:
            presentation_json = await generate_presentation_v2(
                PresentationMarkdownModel(
                    title=presentation_content.title,
                    slides=presentation_content.slides,
                    notes=presentation_content.notes,
                ),
                self.data.slide_mode,
                self.data.model
            )
        except ValueError as e:
            logging_service.logger.error(f"V2 Generation failed: {str(e)}", extra=log_metadata)
            raise HTTPException(status_code=400, detail=str(e))
        
        # Convert to slide models
        slide_models = []
        for i, slide in enumerate(presentation_json["slides"]):
            slide["index"] = i
            slide["presentation"] = self.presentation_id
            slide_model = SlideModel(**slide)
            slide_models.append(slide_model)
        
        # Fetch assets (images, icons)
        print("-" * 40)
        print("V2: Fetching Slide Assets")
        async for result in self.fetch_slide_assets(slide_models):
            print(result)
        
        # Save to database
        slide_sql_models = [
            SlideSqlModel(**each.model_dump(mode="json")) for each in slide_models
        ]
        
        presentation = PresentationSqlModel(
            id=self.presentation_id,
            prompt=self.data.prompt,
            n_slides=self.data.n_slides,
            language=self.data.language,
            summary=self.data.content,
            theme=self.theme,
            title=presentation_content.title,
            outlines=[each.model_dump() for each in presentation_content.slides],
            notes=presentation_content.notes,
            slide_mode=self.data.slide_mode,
        )
        
        with get_sql_session() as sql_session:
            sql_session.add(presentation)
            sql_session.add_all(slide_sql_models)
            sql_session.commit()
            for each in slide_sql_models:
                sql_session.refresh(each)
            sql_session.refresh(presentation)
        
        logging_service.logger.info(
            f"V2 Presentation generated successfully: {self.presentation_id}",
            extra=log_metadata
        )
        
        return {
            "id": self.presentation_id,
            "title": presentation.title,
            "slides": [s.model_dump() for s in slide_sql_models],
            "theme": self.theme,
            "message": "Presentation generated successfully with V2"
        }


@router.post("/generate/presentation")
async def generate_presentation_v2_endpoint(
    prompt: Optional[str] = Form(None),
    n_slides: int = Form(5),
    language: Optional[str] = Form("English"),
    content: Optional[str] = Form(None),
    theme: str = Form("yellow"),
    slide_mode: str = Form("normal"),
    model: Optional[str] = Form(None),
    export_as: Optional[str] = Form(None),
    logging_service: LoggingService = Depends(),
):
    """V2 endpoint for presentation generation with PydanticAI"""
    
    presentation_id = str(uuid.uuid4())
    log_metadata = get_log_metadata(presentation_id)
    
    async def generate():
        # Create request object from form data
        request = GeneratePresentationRequestV2(
            prompt=prompt,
            n_slides=n_slides,
            language=language,
            content=content,
            theme=ThemeNames(theme) if theme else ThemeNames.YELLOW,
            slide_mode=slide_mode,
            model=model
        )
        
        handler = GeneratePresentationHandlerV2(presentation_id, request)
        return await handler.generate(logging_service, log_metadata)
    
    return await handle_errors(
        generate,
        HTTPException(500, "V2 Presentation generation failed"),
        logging_service,
        log_metadata
    )


@router.post("/generate/presentation/stream")
async def generate_presentation_stream_v2_endpoint(
    request: GeneratePresentationRequestV2,
    logging_service: LoggingService,
):
    """V2 streaming endpoint (simulated streaming for now)"""
    
    presentation_id = str(uuid.uuid4())
    log_metadata = get_log_metadata(presentation_id)
    
    logging_service.logger.info(
        f"V2 Stream generation request: {request.model_dump()}",
        extra=log_metadata
    )
    
    async def stream_generator():
        try:
            # Generate outline
            yield f"data: {json.dumps({'status': 'Generating outline...'})}\n\n"
            
            presentation_content = await generate_ppt_content(
                request.prompt,
                request.n_slides,
                request.language,
                request.content,
            )
            
            yield f"data: {json.dumps({'status': 'Generating presentation with AI...'})}\n\n"
            
            # Stream presentation generation
            async for chunk in generate_presentation_stream_v2(
                PresentationMarkdownModel(
                    title=presentation_content.title,
                    slides=presentation_content.slides,
                    notes=presentation_content.notes,
                ),
                request.slide_mode,
                request.model
            ):
                yield chunk
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream"
    )


@router.get("/models")
async def get_available_models():
    """Get list of available models for current provider"""
    from ppt_generator_v2.model_manager import model_manager
    from api.utils.model_utils import get_selected_llm_provider
    from api.models import SelectedLLMProvider
    
    provider = get_selected_llm_provider()
    
    if provider == SelectedLLMProvider.OPENAI:
        models = await model_manager.get_available_openai_models()
    elif provider == SelectedLLMProvider.GOOGLE:
        models = await model_manager.get_available_gemini_models()
    else:
        models = set()
    
    return {
        "provider": provider.value,
        "models": sorted(list(models))
    }