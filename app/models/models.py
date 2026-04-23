from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    id: str | None = None
    role: Literal["user", "assistant"]
    content: str
    stage: str | None = None
    created_at: datetime | None = None
    recurring: bool | None = False


class UserInput(BaseModel):
    assistant_id: str
    user_id: str
    history: list[Message]
    newMessage: Message
    chat_id: str | None = None
    language: str | None = None
    current_stage: str | None = None
    reasoning: str | None = None
    missing_criteria: list[dict[str, str]] | None = None
    app: Literal["coachbot", "studio", "whatsapp"] = "coachbot"


class InitialMessageRequest(BaseModel):
    user_id: str
    assistant_id: str
    recurring: bool = False
    user_name: str | None = None
    language: str | None = None
    last_conversation_date: str | None = None
    conversation_history: list[Message] | None = None


class CoachingResponse(BaseModel):
    chat_id: str
    response: str
