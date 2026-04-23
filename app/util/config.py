import os
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings

from app.util.constants import DB_PARAMS


class Settings(BaseSettings):
    DATABASE_URL: str = f"postgresql://{DB_PARAMS['user']}:{quote_plus(DB_PARAMS['password'])}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "default_openai_api_key")
    ENV: str = os.getenv("ENV", "dev")

    @property
    def DEV_MODE(self) -> bool:
        return self.ENV.lower() == "dev"


settings = Settings()
