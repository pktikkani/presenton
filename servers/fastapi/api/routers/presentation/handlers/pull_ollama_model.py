import json
import traceback
import aiohttp
from fastapi import BackgroundTasks, HTTPException
from api.models import LogMetadata
from api.routers.presentation.handlers.list_supported_ollama_models import (
    SUPPORTED_OLLAMA_MODELS,
)
from api.routers.presentation.models import OllamaModelStatusResponse
from api.services.instances import REDIS_SERVICE
from api.services.logging import LoggingService
from api.utils.model_utils import (
    get_llm_provider_url_or,
    list_pulled_ollama_models,
    pull_ollama_model,
)


class PullOllamaModelHandler:

    def __init__(self, name: str):
        self.name = name

    async def get(
        self,
        logging_service: LoggingService,
        log_metadata: LogMetadata,
        background_tasks: BackgroundTasks,
    ):
        logging_service.logger.info(
            logging_service.message(self.name),
            extra=log_metadata.model_dump(),
        )

        if self.name not in SUPPORTED_OLLAMA_MODELS:
            raise HTTPException(
                status_code=400,
                detail=f"Model {self.name} is not supported",
            )

        try:
            pulled_models = await list_pulled_ollama_models()
            filtered_models = [
                model for model in pulled_models if model.name == self.name
            ]
            if filtered_models:
                return filtered_models[0]
        except HTTPException as e:
            logging_service.logger.warning(
                logging_service.message(e.detail),
                extra=log_metadata.model_dump(),
            )
            raise e
        except Exception as e:
            traceback.print_exc()
            logging_service.logger.warning(
                f"Failed to check pulled models: {e}",
                extra=log_metadata.model_dump(),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to check pulled models: {e}",
            )

        saved_model_status = REDIS_SERVICE.get(f"ollama_models/{self.name}")

        # If the model is being pulled, return the model
        if saved_model_status:
            saved_model_status_json = json.loads(saved_model_status)
            # If the model is being pulled, return the model
            # ? If the model status is pulled in redis but was not found while listing pulled models,
            # ? it means the model was deleted and we need to pull it again
            if (
                saved_model_status_json["status"] == "error"
                or saved_model_status_json["status"] == "pulled"
            ):
                REDIS_SERVICE.delete(f"ollama_models/{self.name}")
            else:
                return saved_model_status_json

        # If the model is not being pulled, pull the model
        background_tasks.add_task(self.pull_model_in_background)

        return OllamaModelStatusResponse(
            name=self.name,
            status="pulling",
            done=False,
        )

    async def pull_model_in_background(self):
        await self.pull_model()

    async def pull_model(self):
        saved_model_status = OllamaModelStatusResponse(
            name=self.name,
            status="pulling",
            done=False,
        )
        log_event_count = 0

        try:
            async for event in pull_ollama_model(self.name):
                log_event_count += 1
                if log_event_count != 1 and log_event_count % 20 != 0:
                    continue

                if "completed" in event:
                    saved_model_status.downloaded = event["completed"]

                if not saved_model_status.size and "total" in event:
                    saved_model_status.size = event["total"]

                if "status" in event:
                    saved_model_status.status = event["status"]

                REDIS_SERVICE.set(
                    f"ollama_models/{self.name}",
                    json.dumps(saved_model_status.model_dump(mode="json")),
                )

        except Exception as e:
            saved_model_status.status = "error"
            saved_model_status.done = True
            REDIS_SERVICE.set(
                f"ollama_models/{self.name}",
                json.dumps(saved_model_status.model_dump(mode="json")),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to pull model: {e}",
            )

        saved_model_status.done = True
        saved_model_status.status = "pulled"
        saved_model_status.downloaded = saved_model_status.size

        REDIS_SERVICE.set(
            f"ollama_models/{self.name}",
            json.dumps(saved_model_status.model_dump(mode="json")),
        )

        return saved_model_status
