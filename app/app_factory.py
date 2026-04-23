from dotenv import load_dotenv
from fastapi import FastAPI

from app.api.router import router
from app.middleware.middleware import setup_all_middleware

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(title="CoachBotAI GenAI Backend")

    setup_all_middleware(app)

    app.include_router(router)

    return app
