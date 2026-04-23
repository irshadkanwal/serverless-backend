from pydantic import BaseModel


class LLMConfig(BaseModel):
    model: str | None = None
    temperature: float | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
