from pydantic import BaseModel


class CoachingRequest(BaseModel):
    messages: list[dict[str, str]]
    instructions: str
    user_id: str
    tone_examples: str | None = None
    workspace: str | None = None
    knowledge_ids: list[str] | None = None
    is_initial_message: bool = False
