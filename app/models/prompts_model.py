from pydantic import BaseModel


class PromptUpdate(BaseModel):
    content: str


class PromptResponse(BaseModel):
    content: str
    type: str
    name: str
