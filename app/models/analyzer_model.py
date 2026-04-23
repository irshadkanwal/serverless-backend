from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    session_history: list[dict[str, str]]
    stage_history: list[dict[str, str]]
    current_stage: str
    metadata: dict | None = None


class StageDetail(BaseModel):
    """Represents detailed stage information including next stage"""

    id: str
    name: str
    instructions: str | None = None
    analyzer: str | None = None
    order: int
    next_stage_name: str | None = None


class StageTransitionResult(BaseModel):
    """Stage transition analysis results model"""

    current_stage: str
    next_stage: str | None
    transition_required: bool = Field(
        description="Flag indicating if transition is required"
    )
    transition_direction: str = Field(description="Direction of the transition")
    reasoning: str = Field(description="Reasoning for the classification")
    criteria_missing: list[dict[str, str]] = Field(
        description="Criteria that are not met for transition"
    )
    confidence: float = Field(
        description="Confidence score (0-1) for the transition decision"
    )
    return_indicators: dict[str, int] = Field(
        description="Return indicators for the transition decision"
    )


class EmotionalShift(BaseModel):
    from_emotion: str
    to_emotion: str
    trigger: str
    confidence: float = Field(ge=0.0, le=1.0)


class EmotionalAnalysisResult(BaseModel):
    primary_emotion: str
    emotion_intensity: float = Field(ge=0.0, le=1.0)
    emotional_trajectory: str
    confidence: float = Field(ge=0.0, le=1.0)
    emotional_shifts: list[EmotionalShift]
    supporting_evidence: list[str]
    recommendations: list[str]
    patterns: dict[str, list[str]] | None = Field(
        description="Recurring emotional patterns with examples"
    )


class ContextNeedResult(BaseModel):
    context_required: bool
    relevance_score: float = Field(ge=0.0, le=1.0)
    topics_for_context: list[str]
    rationale: str
    context_priority: str = Field(description="Priority level for context retrieval")


class ContentTopic(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    key_points: list[str]
    evidence: list[str]


class LifeArea(BaseModel):
    area: str
    relevance: float = Field(ge=0.0, le=1.0)
    topics: list[str]
    insights: list[str]


class ContentAnalysisResult(BaseModel):
    topics: list[ContentTopic]
    life_areas: list[LifeArea]
    primary_focus: str
    content_progression: str
    cross_area_insights: list[str]


STAGE_TRANSITION_INDICATORS = [
    "multiple stages",
    "skip",
    "jumping",
    "addressing",
    "covered",
    "accomplish",
    "progress",
    "multi",
    "several",
    "multiple tasks",
]
