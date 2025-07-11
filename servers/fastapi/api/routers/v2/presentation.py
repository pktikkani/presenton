"""V2 Presentation API endpoints with enhanced features"""
import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse

from api.routers.v2.models import (
    GeneratePresentationRequestV2,
    AvailableModelsResponse,
    SlideMode,
    ImageProvider,
    FluxModel
)
from api.routers.presentation.models import (
    PresentationPathAndEditPath,
    ThemeEnum
)
from api.request_utils import RequestUtils
from api.utils.utils import handle_errors
from api.utils.model_utils_v2 import model_manager_v2
from api.models import SelectedLLMProvider
from api.utils.model_utils import get_selected_llm_provider

# Import V1 handler and modify for V2
from api.routers.presentation.handlers.generate_presentation import GeneratePresentationHandler
from api.routers.presentation.models import GeneratePresentationRequest

router = APIRouter(prefix="/api/v2/ppt", tags=["presentation-v2"])


@router.post("/generate/presentation", response_model=PresentationPathAndEditPath)
async def generate_presentation_v2(
    prompt: Annotated[str, Form(...)],
    n_slides: Annotated[int, Form()] = 8,
    language: Annotated[str, Form()] = "English",
    theme: Annotated[str, Form()] = "light",
    slide_mode: Annotated[str, Form()] = "normal",
    model: Annotated[Optional[str], Form()] = None,
    image_provider: Annotated[Optional[str], Form()] = None,
    flux_model: Annotated[Optional[str], Form()] = None,
    export_as: Annotated[str, Form()] = "pptx",
):
    """Enhanced presentation generation with V2 features"""
    presentation_id = str(uuid.uuid4())
    request_utils = RequestUtils(f"/api/v2/ppt/generate/presentation")
    logging_service, log_metadata = await request_utils.initialize_logger(
        presentation_id=presentation_id,
    )
    
    try:
        # Validate inputs
        slide_mode_enum = SlideMode(slide_mode)
        theme_enum = ThemeEnum(theme if theme else "light")
        
        # Validate model if specified
        if model:
            validated_model = await model_manager_v2.validate_model(model)
        else:
            validated_model = None
        
        # Validate image provider
        image_provider_enum = None
        if image_provider:
            image_provider_enum = ImageProvider(image_provider)
        
        # Validate Flux model if using Flux
        flux_model_enum = None
        if flux_model and image_provider == "flux":
            flux_model_enum = FluxModel(flux_model)
        
        # Create V1 compatible request
        v1_request = GeneratePresentationRequest(
            prompt=prompt,
            n_slides=n_slides,
            language=language,
            theme=theme_enum,
            export_as=export_as
        )
        
        # Create enhanced V2 handler
        handler = GeneratePresentationHandlerV2(
            presentation_id=presentation_id,
            data=v1_request,
            slide_mode=slide_mode_enum,
            model=validated_model,
            image_provider=image_provider_enum,
            flux_model=flux_model_enum
        )
        
        return await handle_errors(
            handler.post,
            logging_service,
            log_metadata,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models", response_model=AvailableModelsResponse)
async def get_available_models():
    """Get list of available models for current provider"""
    provider = get_selected_llm_provider()
    
    if provider == SelectedLLMProvider.OPENAI:
        models = await model_manager_v2.get_available_openai_models()
        default = "gpt-4o"
    elif provider == SelectedLLMProvider.GOOGLE:
        models = await model_manager_v2.get_available_google_models()
        default = "gemini-2.0-flash"
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Model listing not available for provider: {provider.value}"
        )
    
    return AvailableModelsResponse(
        provider=provider.value,
        models=sorted(list(models)),
        default_model=default
    )


# Enhanced V2 handler that extends V1
class GeneratePresentationHandlerV2(GeneratePresentationHandler):
    """Enhanced presentation handler with V2 features"""
    
    def __init__(
        self,
        presentation_id: str,
        data: GeneratePresentationRequest,
        slide_mode: SlideMode,
        model: Optional[str] = None,
        image_provider: Optional[ImageProvider] = None,
        flux_model: Optional[FluxModel] = None
    ):
        super().__init__(presentation_id, data)
        self.slide_mode = slide_mode
        self.model = model
        self.image_provider = image_provider
        self.flux_model = flux_model
        
        # Store V2 config in session for use by generators
        self.v2_config = {
            "slide_mode": slide_mode.value,
            "model": model,
            "image_provider": image_provider.value if image_provider else None,
            "flux_model": flux_model.value if flux_model else None
        }
    
    async def post(self, logging_service, log_metadata):
        """Override to inject V2 configuration"""
        # Inject V2 config into environment or context
        import os
        if self.model:
            os.environ["V2_MODEL_OVERRIDE"] = self.model
        if self.slide_mode:
            os.environ["V2_SLIDE_MODE"] = self.slide_mode.value
        if self.image_provider:
            os.environ["V2_IMAGE_PROVIDER"] = self.image_provider.value
        if self.flux_model:
            os.environ["V2_FLUX_MODEL"] = self.flux_model.value
        
        try:
            # Call parent implementation
            result = await super().post(logging_service, log_metadata)
            return result
        finally:
            # Clean up environment
            for key in ["V2_MODEL_OVERRIDE", "V2_SLIDE_MODE", "V2_IMAGE_PROVIDER", "V2_FLUX_MODEL"]:
                os.environ.pop(key, None)