from pydantic import BaseModel

from app.models.llm_config_model import LLMConfig


class StageData(BaseModel):
    name: str
    instructions: str
    analyzer: str
    is_first: bool


class AICoachSetup(BaseModel):
    userId: str
    assistantConfigurationId: str
    instructions: str | None
    stage: StageData | None = None
    recurring: bool = False
    llm_config: LLMConfig | None = None
    knowledge_ids: list[str] | None = None
    onboarding: str | None = None
    onboarding_analyzer: str | None = None
    tone: str | None = None
    guidelines: str | None = None
    tone_examples: str | None = None
