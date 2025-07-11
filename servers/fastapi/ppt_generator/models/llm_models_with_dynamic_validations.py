from typing import List, Type, Dict, Any
from pydantic import Field, create_model, BaseModel

from graph_processor.models import LLMGraphModel
from ppt_generator.models.content_type_models import TableType
from ppt_generator.models.other_models import (
    TYPE1, TYPE2, TYPE3, TYPE4, TYPE5, TYPE6, TYPE7, TYPE8, TYPE9
)
from ppt_generator.models.llm_models import (
    LLMTableDataModel, LLMTableModel, LLMHeadingModel,
    LLMHeadingModelWithImagePrompt, LLMHeadingModelWithIconQuery,
    LLMSlideContentModel, LLMType1Content, LLMType2Content,
    LLMType3Content, LLMType4Content, LLMType5Content,
    LLMType6Content, LLMType7Content, LLMType8Content,
    LLMType9Content, LLMSlideModel, LLMPresentationModel
)
from ppt_generator.slide_mode_config import get_limits_for_mode


def create_dynamic_validation_model(
    base_model: Type[BaseModel],
    field_configs: Dict[str, Dict[str, Any]],
    mode: str = "normal"
) -> Type[BaseModel]:
    """Create a dynamic validation model with mode-specific limits"""
    
    limits = get_limits_for_mode(mode)
    new_fields = {}
    
    # Copy existing fields and update with new constraints
    for field_name, field_info in base_model.__fields__.items():
        if field_name in field_configs:
            config = field_configs[field_name]
            limit_key = config.get("limit_key", field_name)
            
            if limit_key in limits:
                new_fields[field_name] = (
                    field_info.type_,
                    Field(
                        description=field_info.field_info.description,
                        min_length=limits[limit_key]["min"],
                        max_length=limits[limit_key]["max"]
                    )
                )
            else:
                # Keep original field if no limit config
                new_fields[field_name] = (field_info.type_, field_info.field_info)
        else:
            # Keep original field
            new_fields[field_name] = (field_info.type_, field_info.field_info)
    
    # Create new model class
    model_name = f"{base_model.__name__}_{mode}"
    return create_model(model_name, __base__=base_model, **new_fields)


def get_llm_content_type_mapping_with_validation(mode: str = "normal") -> Dict[int, Type[BaseModel]]:
    """Get content type mapping with mode-specific validations"""
    
    limits = get_limits_for_mode(mode)
    
    # Define field configurations for each model type
    field_configs = {
        "title": {"limit_key": "title"},
        "body": {"limit_key": "body"},
        "description": {"limit_key": "description"},
        "item_title": {"limit_key": "item_title"},
        "item_description": {"limit_key": "item_description"},
        "image_prompt": {"limit_key": "image_prompt"},
        "icon_query": {"limit_key": "icon_query"},
    }
    
    # Create dynamic models for each content type
    LLMType1ContentValidation = create_dynamic_validation_model(
        LLMType1Content,
        {"body": field_configs["body"], "image_prompt": field_configs["image_prompt"]},
        mode
    )
    
    LLMType2ContentValidation = create_dynamic_validation_model(
        LLMType2Content,
        {
            "items": {
                "limit_key": "items",
                "max_items": limits["max_items"]
            }
        },
        mode
    )
    
    # For types with items, we need special handling
    class LLMHeadingModelValidation(LLMHeadingModel):
        title: str = Field(
            description=f"Item title in about {limits['item_title']['max'] // 10} words.",
            min_length=limits["item_title"]["min"],
            max_length=limits["item_title"]["max"],
        )
        description: str = Field(
            description=f"Item description in about {limits['item_description']['max'] // 5} words.",
            min_length=limits["item_description"]["min"],
            max_length=limits["item_description"]["max"],
        )
    
    class LLMHeadingModelWithImagePromptValidation(LLMHeadingModelWithImagePrompt):
        image_prompt: str = Field(
            description=f"Item image prompt in about {limits['image_prompt']['max'] // 10} words",
            min_length=limits["image_prompt"]["min"],
            max_length=limits["image_prompt"]["max"],
        )
        title: str = Field(
            description=f"Item title in about {limits['item_title']['max'] // 10} words.",
            min_length=limits["item_title"]["min"],
            max_length=limits["item_title"]["max"],
        )
        description: str = Field(
            description=f"Item description in about {limits['item_description']['max'] // 5} words.",
            min_length=limits["item_description"]["min"],
            max_length=limits["item_description"]["max"],
        )
    
    class LLMHeadingModelWithIconQueryValidation(LLMHeadingModelWithIconQuery):
        icon_query: str = Field(
            description=f"Item icon query in about {limits['icon_query']['max'] // 10} words",
            min_length=limits["icon_query"]["min"],
            max_length=limits["icon_query"]["max"],
        )
        title: str = Field(
            description=f"Item title in about {limits['item_title']['max'] // 10} words.",
            min_length=limits["item_title"]["min"],
            max_length=limits["item_title"]["max"],
        )
        description: str = Field(
            description=f"Item description in about {limits['item_description']['max'] // 5} words.",
            min_length=limits["item_description"]["min"],
            max_length=limits["item_description"]["max"],
        )
    
    class LLMSlideContentModelValidation(LLMSlideContentModel):
        title: str = Field(
            description=f"Slide title in about {limits['title']['max'] // 10} words",
            min_length=limits["title"]["min"],
            max_length=limits["title"]["max"],
        )
    
    class LLMType1ContentValidation(LLMType1Content):
        body: str = Field(
            description=f"Slide content summary in about {limits['body']['max'] // 10} words.",
            min_length=limits["body"]["min"],
            max_length=limits["body"]["max"],
        )
        image_prompt: str = Field(
            description=f"Slide image prompt in about {limits['image_prompt']['max'] // 10} words",
            min_length=limits["image_prompt"]["min"],
            max_length=limits["image_prompt"]["max"],
        )
    
    # Type 2-4 use items with different heading models
    class LLMType2ContentValidation(LLMType2Content):
        items: List[LLMHeadingModelValidation] = Field(
            description=f"List of items (max {limits['max_items']})",
            min_length=1,
            max_length=limits["max_items"],
        )
    
    class LLMType3ContentValidation(LLMType3Content):
        items: List[LLMHeadingModelWithImagePromptValidation] = Field(
            description=f"List of items (max {limits['max_items']})",
            min_length=1,
            max_length=limits["max_items"],
        )
    
    class LLMType4ContentValidation(LLMType4Content):
        items: List[LLMHeadingModelWithIconQueryValidation] = Field(
            description=f"List of items (max {limits['max_items']})",
            min_length=1,
            max_length=limits["max_items"],
        )
    
    # Type 6-8 have body content
    class LLMType6ContentValidation(LLMType6Content):
        items: List[LLMHeadingModelValidation] = Field(
            description=f"List of items (max {limits['max_items']})",
            min_length=1,
            max_length=limits["max_items"],
        )
        body: str = Field(
            description=f"Slide content summary in about {limits['body']['max'] // 10} words.",
            min_length=limits["body"]["min"],
            max_length=limits["body"]["max"],
        )
    
    class LLMType7ContentValidation(LLMType7Content):
        items: List[LLMHeadingModelWithImagePromptValidation] = Field(
            description=f"List of items (max {limits['max_items']})",
            min_length=1,
            max_length=limits["max_items"],
        )
        body: str = Field(
            description=f"Slide content summary in about {limits['body']['max'] // 10} words.",
            min_length=limits["body"]["min"],
            max_length=limits["body"]["max"],
        )
    
    class LLMType8ContentValidation(LLMType8Content):
        items: List[LLMHeadingModelWithIconQueryValidation] = Field(
            description=f"List of items (max {limits['max_items']})",
            min_length=1,
            max_length=limits["max_items"],
        )
        body: str = Field(
            description=f"Slide content summary in about {limits['body']['max'] // 10} words.",
            min_length=limits["body"]["min"],
            max_length=limits["body"]["max"],
        )
    
    # Return mapping
    return {
        TYPE1: LLMType1ContentValidation,
        TYPE2: LLMType2ContentValidation,
        TYPE3: LLMType3ContentValidation,
        TYPE4: LLMType4ContentValidation,
        TYPE5: LLMType5Content,  # Graph types don't need text validation
        TYPE6: LLMType6ContentValidation,
        TYPE7: LLMType7ContentValidation,
        TYPE8: LLMType8ContentValidation,
        TYPE9: LLMType9Content,  # Table type has its own structure
    }