from typing import Any

from pydantic import BaseModel

from app.models.models import Message


class StageSummaryContent(BaseModel):
    messages: list[Message]
    stage: str
    detail: str
    previous_summary: dict | None = None


class SessionSummaryContent(BaseModel):
    chat_id: str
    stage_summaries: list[dict]
    messages: list[Message]


class SessionSummary(BaseModel):
    chat_id: str
    overall_progress: str
    key_milestones: list[str]
    stage_insights: dict[str, list[str]]
    client_evolution: dict[str, str]
    action_items: list[str]
    recommendations: list[str]
    metadata: dict[str, Any]
