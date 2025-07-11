"""V2 API Models with enhanced features"""
from enum import Enum
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from api.routers.presentation.models import ThemeEnum


class SlideMode(str, Enum):
    """Enhanced slide modes with better differentiation"""
    COMPACT = "compact"
    NORMAL = "normal"
    DETAILED = "detailed"


class ImageProvider(str, Enum):
    """Available image generation providers"""
    OPENAI = "openai"
    GOOGLE = "google"
    FLUX = "flux"
    PEXELS = "pexels"


class FluxModel(str, Enum):
    """Available Flux models"""
    KONTEXT_MAX = "kontext-max"
    KONTEXT_PRO = "kontext-pro"
    PRO_1_1_ULTRA = "pro-1.1-ultra"
    PRO_1_1 = "pro-1.1"
    PRO = "pro"
    DEV = "dev"


class GeneratePresentationRequestV2(BaseModel):
    """Enhanced presentation generation request with V2 features"""
    prompt: str = Field(..., min_length=10, description="Main prompt for presentation")
    n_slides: int = Field(default=8, ge=3, le=20, description="Number of slides")
    language: str = Field(default="English", description="Language for presentation")
    theme: ThemeEnum = Field(default=ThemeEnum.LIGHT, description="Visual theme")
    slide_mode: SlideMode = Field(default=SlideMode.NORMAL, description="Content density mode")
    
    # Model selection
    model: Optional[str] = Field(None, description="Specific LLM model to use (e.g., gpt-4o, gpt-4o-mini)")
    
    # Image generation
    image_provider: Optional[ImageProvider] = Field(None, description="Image generation provider")
    flux_model: Optional[FluxModel] = Field(None, description="Specific Flux model if using Flux")
    
    # Export options
    export_as: Literal["pptx", "pdf"] = Field(default="pptx")
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Basic validation - actual model validation will happen in the handler"""
        if v and len(v) < 3:
            raise ValueError("Model name too short")
        return v


class AvailableModelsResponse(BaseModel):
    """Response containing available models for a provider"""
    provider: str
    models: List[str]
    default_model: str


class ModelInfo(BaseModel):
    """Detailed information about a model"""
    id: str
    name: str
    provider: str
    context_length: Optional[int] = None
    description: Optional[str] = None
    pricing: Optional[dict] = None