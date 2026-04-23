from enum import Enum

from pydantic import BaseModel, Field


class ModerationRule(BaseModel):
    id: str | None = Field(default=None, description="ID of the moderation rule")
    name: str = Field(default="", description="Name of the moderation rule")
    allow_category: str | None = Field(
        default="", description="Allow category of the moderation rule"
    )
    input_score: float | None = Field(
        default=0.0, description="Score threshold for input moderation"
    )
    output_score: float | None = Field(
        default=0.0, description="Score threshold for output moderation"
    )
    response_examples: str | None = Field(
        default=None, description="Response examples for template generation"
    )


class ModerationResult(BaseModel):
    is_safe: bool = Field(description="Flag indicating if the content is safe")
    response: str | None = Field(default=None, description="Moderation response")


class ModerationType(Enum):
    INPUT = "input"
    OUTPUT = "output"
