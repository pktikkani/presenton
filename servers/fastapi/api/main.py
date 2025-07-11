import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from api.models import SelectedLLMProvider
from api.routers.presentation.router import presentation_router
from api.services.database import sql_engine
from api.utils.utils import update_env_with_user_config
from api.utils.model_utils import get_selected_llm_provider

can_change_keys = os.getenv("CAN_CHANGE_KEYS") != "false"


async def check_llm_model_availability():
    if not can_change_keys:
        if get_selected_llm_provider() == SelectedLLMProvider.OPENAI:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise Exception("OPENAI_API_KEY must be provided")

        elif get_selected_llm_provider() == SelectedLLMProvider.GOOGLE:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise Exception("GOOGLE_API_KEY must be provided")



@asynccontextmanager
async def lifespan(_: FastAPI):
    os.makedirs(os.getenv("APP_DATA_DIRECTORY"), exist_ok=True)
    SQLModel.metadata.create_all(sql_engine)
    await check_llm_model_availability()
    yield


app = FastAPI(lifespan=lifespan)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def update_env_middleware(request: Request, call_next):
    if can_change_keys:
        update_env_with_user_config()
    return await call_next(request)


app.include_router(presentation_router)
