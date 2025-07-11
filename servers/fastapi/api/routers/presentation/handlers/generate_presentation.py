import json
import os
from typing import List
import uuid, asyncio
from fastapi import HTTPException
from api.models import LogMetadata
from api.routers.presentation.handlers.export_as_pptx import ExportAsPptxHandler
from api.routers.presentation.handlers.upload_files import UploadFilesHandler
from api.routers.presentation.mixins.fetch_assets_on_generation import (
    FetchAssetsOnPresentationGenerationMixin,
)
from api.routers.presentation.models import (
    ExportAsRequest,
    GeneratePresentationRequest,
    PresentationAndPath,
    PresentationPathAndEditPath,
)
from api.services.database import get_sql_session
from api.services.instances import TEMP_FILE_SERVICE
from api.services.logging import LoggingService
from api.sql_models import PresentationSqlModel, SlideSqlModel
from api.utils.utils import get_presentation_dir
from api.utils.model_utils import is_custom_llm_selected, is_ollama_selected
from document_processor.loader import DocumentsLoader
from ppt_config_generator.document_summary_generator import generate_document_summary
from ppt_config_generator.models import PresentationMarkdownModel
from ppt_config_generator.ppt_outlines_generator import generate_ppt_content
from ppt_generator.generator import generate_presentation
from ppt_generator.models.llm_models import (
    LLM_CONTENT_TYPE_MAPPING,
)
from ppt_generator.models.slide_model import SlideModel


class GeneratePresentationHandler(FetchAssetsOnPresentationGenerationMixin):

    def __init__(self, presentation_id: str, data: GeneratePresentationRequest):
        self.session = str(uuid.uuid4())
        self.presentation_id = presentation_id
        self.data = data

        self.temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
        self.presentation_dir = get_presentation_dir(self.presentation_id)

    def __del__(self):
        TEMP_FILE_SERVICE.cleanup_temp_dir(self.temp_dir)

    async def post(self, logging_service: LoggingService, log_metadata: LogMetadata):
        documents_and_images_path = await UploadFilesHandler(
            documents=self.data.documents,
            images=None,
        ).post(logging_service, log_metadata)

        summary = None
        if documents_and_images_path.documents:
            documents_loader = DocumentsLoader(documents_and_images_path.documents)
            await documents_loader.load_documents(self.temp_dir)

            print("-" * 40)
            print("Generating Document Summary")
            summary = await generate_document_summary(documents_loader.documents)

        print("-" * 40)
        print("Generating PPT Outline")
        print(f"Requested slides: {self.data.n_slides}")
        print(f"Language: {self.data.language}")
        presentation_content = await generate_ppt_content(
            self.data.prompt,
            self.data.n_slides,
            self.data.language,
            summary,
        )
        print(f"Generated slides count: {len(presentation_content.slides)}")
        for i, slide in enumerate(presentation_content.slides):
            print(f"  Slide {i+1}: {slide.title}")

        print("-" * 40)
        print("Generating Presentation")
        presentation_text = await generate_presentation(
            PresentationMarkdownModel(
                title=presentation_content.title,
                slides=presentation_content.slides,
                notes=presentation_content.notes,
            )
        )

        print("-" * 40)
        print("Parsing Presentation")
        print(f"Raw presentation text length: {len(presentation_text)}")
        
        try:
            presentation_json = json.loads(presentation_text)
            print(f"Successfully parsed JSON with {len(presentation_json.get('slides', []))} slides")
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {e}")
            print(f"First 500 chars of response: {presentation_text[:500]}")
            raise

        slide_models: List[SlideModel] = []
        for i, slide in enumerate(presentation_json["slides"]):
            print(f"\nProcessing slide {i+1}/{len(presentation_json['slides'])}")
            print(f"Slide type: {slide.get('type', 'unknown')}")
            
            slide["index"] = i
            slide["presentation"] = self.presentation_id
            
            # Log slide content structure
            if "content" in slide:
                print(f"Content keys: {list(slide['content'].keys())}")
                
                # Handle missing fields based on slide type
                if slide["type"] == 2 and "body" in slide["content"]:
                    print(f"Type 2 slide with {len(slide['content']['body'])} body items")
                    
                    # Check if we have alternating heading/description pattern
                    body_items = slide["content"]["body"]
                    has_alternating_pattern = True
                    for j, item in enumerate(body_items):
                        if isinstance(item, dict):
                            if j % 2 == 0 and "heading" not in item:
                                has_alternating_pattern = False
                                break
                            elif j % 2 == 1 and "description" not in item:
                                has_alternating_pattern = False
                                break
                    
                    if has_alternating_pattern and len(body_items) % 2 == 0:
                        # Combine alternating items into proper heading/description pairs
                        print("  Detected alternating heading/description pattern. Combining...")
                        new_body = []
                        for j in range(0, len(body_items), 2):
                            combined_item = {}
                            if j < len(body_items) and isinstance(body_items[j], dict):
                                combined_item.update(body_items[j])
                            if j + 1 < len(body_items) and isinstance(body_items[j + 1], dict):
                                combined_item.update(body_items[j + 1])
                            new_body.append(combined_item)
                        slide["content"]["body"] = new_body
                        print(f"  Combined into {len(new_body)} complete items")
                    
                    # Now handle any remaining missing fields
                    for j, item in enumerate(slide["content"]["body"]):
                        if isinstance(item, dict):
                            print(f"  Item {j}: keys = {list(item.keys())}")
                            if "description" not in item:
                                print(f"  WARNING: Missing description in item {j}")
                                # Generate a default description based on the heading
                                heading = item.get("heading", "")
                                item["description"] = f"Details about {heading}"
                                print(f"  Generated default description: {item['description']}")
                
                elif slide["type"] == 4 and "body" in slide["content"]:
                    print(f"Type 4 slide with {len(slide['content']['body'])} body items")
                    for j, item in enumerate(slide["content"]["body"]):
                        if isinstance(item, dict):
                            print(f"  Item {j}: keys = {list(item.keys())}")
                            if "image_prompt" not in item:
                                print(f"  WARNING: Missing image_prompt in item {j}")
                                # Generate a default image prompt based on the heading
                                heading = item.get("heading", "")
                                item["image_prompt"] = f"Professional image representing {heading}, no text in image"
                                print(f"  Generated default image_prompt: {item['image_prompt']}")
                            if "description" not in item:
                                print(f"  WARNING: Missing description in item {j}")
                                heading = item.get("heading", "")
                                item["description"] = f"Details about {heading}"
                                print(f"  Generated default description: {item['description']}")
                
                elif slide["type"] in [6, 7, 8] and "body" in slide["content"]:
                    print(f"Type {slide['type']} slide with {len(slide['content']['body'])} body items")
                    
                    # Check if we have alternating heading/description pattern
                    body_items = slide["content"]["body"]
                    has_alternating_pattern = True
                    for j, item in enumerate(body_items):
                        if isinstance(item, dict):
                            if j % 2 == 0 and "heading" not in item:
                                has_alternating_pattern = False
                                break
                            elif j % 2 == 1 and "description" not in item:
                                has_alternating_pattern = False
                                break
                    
                    if has_alternating_pattern and len(body_items) % 2 == 0:
                        # Combine alternating items into proper heading/description pairs
                        print("  Detected alternating heading/description pattern. Combining...")
                        new_body = []
                        for j in range(0, len(body_items), 2):
                            combined_item = {}
                            if j < len(body_items) and isinstance(body_items[j], dict):
                                combined_item.update(body_items[j])
                            if j + 1 < len(body_items) and isinstance(body_items[j + 1], dict):
                                combined_item.update(body_items[j + 1])
                            new_body.append(combined_item)
                        slide["content"]["body"] = new_body
                        print(f"  Combined into {len(new_body)} complete items")
                    
                    # Now handle any remaining missing fields
                    for j, item in enumerate(slide["content"]["body"]):
                        if isinstance(item, dict):
                            print(f"  Item {j}: keys = {list(item.keys())}")
                            if "description" not in item:
                                print(f"  WARNING: Missing description in item {j}")
                                heading = item.get("heading", "")
                                item["description"] = f"Details about {heading}"
                                print(f"  Generated default description: {item['description']}")
                            
                            # Type 7 and 8 need icon_query
                            if slide["type"] in [7, 8] and "icon_query" not in item:
                                print(f"  WARNING: Missing icon_query in item {j}")
                                heading = item.get("heading", "")
                                # Extract first meaningful word for icon
                                icon_word = heading.split()[0] if heading else "info"
                                item["icon_query"] = [icon_word, "icon", "symbol"]
                                print(f"  Generated default icon_query: {item['icon_query']}")
            
            try:
                slide["content"] = (
                    LLM_CONTENT_TYPE_MAPPING[slide["type"]](**slide["content"])
                    .to_content()
                    .model_dump(mode="json")
                )
                print(f"Successfully processed slide {i+1}")
            except Exception as e:
                print(f"\nERROR processing slide {i+1}:")
                print(f"  Exception type: {type(e).__name__}")
                print(f"  Exception message: {str(e)}")
                print(f"  Slide type: {slide.get('type', 'unknown')}")
                print(f"  Full slide data:")
                print(json.dumps(slide, indent=2, ensure_ascii=False))
                raise
                
            # Ensure slide has an ID
            if "id" not in slide or not slide["id"]:
                slide["id"] = str(uuid.uuid4())
            
            slide_model = SlideModel(**slide)
            slide_models.append(slide_model)

        print("-" * 40)
        print("Loading Theme Colors")
        from api.utils.theme_data import get_theme_from_name
        self.theme = get_theme_from_name(self.data.theme.value)

        print("-" * 40)
        print("Fetching Slide Assets")
        # Use image provider from request or construct from image_model
        image_provider = self.data.image_provider
        if not image_provider and self.data.image_model:
            # If image_model is specified but not provider, assume it's a Flux model
            image_provider = f"flux:{self.data.image_model}"
        
        async for result in self.fetch_slide_assets(slide_models, image_provider=image_provider):
            print(result)

        slide_sql_models = [
            SlideSqlModel(**each.model_dump(mode="json")) for each in slide_models
        ]

        presentation = PresentationSqlModel(
            id=self.presentation_id,
            prompt=self.data.prompt,
            n_slides=self.data.n_slides,
            language=self.data.language,
            summary=summary,
            theme=self.theme,
            title=presentation_content.title,
            outlines=[each.model_dump() for each in presentation_content.slides],
            notes=presentation_content.notes,
        )

        with get_sql_session() as sql_session:
            sql_session.add(presentation)
            sql_session.add_all(slide_sql_models)
            sql_session.commit()
            for each in slide_sql_models:
                sql_session.refresh(each)
            
            # Verify the presentation was saved
            print(f"Presentation saved with ID: {self.presentation_id}")
            print(f"Number of slides saved: {len(slide_sql_models)}")
            
            # Double-check by querying it back
            saved_presentation = sql_session.get(PresentationSqlModel, self.presentation_id)
            if saved_presentation:
                print(f"Verified: Presentation found in DB with title: {saved_presentation.title}")
                # Query slides separately
                from sqlmodel import select
                slides_count = len(sql_session.exec(
                    select(SlideSqlModel).where(SlideSqlModel.presentation == self.presentation_id)
                ).all())
                print(f"Verified: {slides_count} slides in DB for this presentation")
            else:
                print("ERROR: Presentation not found in database after save!")

        if self.data.export_as == "pptx":
            print("-" * 40)
            print("Preparing PPTX Export")
            
            # For API-only mode, we create the export request directly
            # without fetching slide metadata from the frontend
            from ppt_generator.models.pptx_models import PptxPresentationModel, PptxSlideModel
            
            # Convert slide models to PPTX format
            pptx_slides = []
            for slide in slide_models:
                pptx_slide = PptxSlideModel(
                    id=slide.id,
                    type=slide.type,
                    content=slide.content,
                    index=slide.index
                )
                pptx_slides.append(pptx_slide)
            
            # Create PPTX presentation model
            pptx_model = PptxPresentationModel(
                id=self.presentation_id,
                title=presentation_content.title,
                slides=pptx_slides,
                theme=self.theme
            )
            
            print("-" * 40)
            print("Exporting Presentation")
            export_request = ExportAsRequest(
                presentation_id=self.presentation_id,
                pptx_model=pptx_model
            )

            presentation_and_path = await ExportAsPptxHandler(export_request).post(
                logging_service, log_metadata
            )

        else:
            # PDF export not supported in API-only mode
            raise HTTPException(
                status_code=400,
                detail="PDF export is not supported in API-only mode. Please use 'pptx' format instead."
            )
        # Convert file path to download URL
        download_url = None
        if presentation_and_path.path:
            # Extract the path after /app/
            path_parts = presentation_and_path.path.split('/app/')
            if len(path_parts) > 1:
                relative_path = path_parts[1]
                # For API-only mode, use the FastAPI static endpoint
                download_url = f"/api/v1/static/{relative_path}"
        
        return PresentationPathAndEditPath(
            **presentation_and_path.model_dump(),
            edit_path=f"/presentation?id={self.presentation_id}",
            download_url=download_url,
        )
