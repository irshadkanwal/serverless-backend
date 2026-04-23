import json

from app.agents.base_agent import BaseAgent
from app.models.models import Message
from app.models.summary_models import StageSummaryContent
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.util.helpers import get_logger, handle_exceptions

logger = get_logger(__name__)


### TODO: Re-Implement the StageSummaryAgent class with a new instruction approach
### + stage analysis
class StageSummaryAgent(BaseAgent[StageSummaryContent, str]):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompts = PromptLoader()

    @handle_exceptions
    def process(self, request: StageSummaryContent) -> str:
        """Generate summary for a specific coaching stage"""
        stage_context = []
        system_message = self._get_stage_summary_prompt(request.stage)
        message_history = self._format_conversation_history(request.messages)
        stage_context.append(system_message)
        stage_context.extend(message_history)

        if request.previous_summary:
            try:
                previous_summary = (
                    json.loads(request.previous_summary)
                    if isinstance(request.previous_summary, str)
                    else request.previous_summary
                )
                summary_context = {
                    "role": "system",
                    "content": json.dumps(previous_summary),
                }
                stage_context.insert(1, summary_context)
            except Exception as e:
                logger.error(f"Error processing previous summary: {e!s}")

        return self.llm_service.generate_json_response(stage_context)

    @handle_exceptions
    def _get_stage_summary_prompt(self, stage: str) -> dict[str, str]:
        """Get stage-specific summary prompt"""
        return {
            "role": "system",
            "content": self.prompts.get_prompt(
                "summary", "stage-summary-system-message"
            ).render(
                stage
            ),  ## TODO: extract key insights from the stage instructions and analysis
        }

    @handle_exceptions
    def _format_conversation_history(
        self, messages: list[Message]
    ) -> list[dict[str, str]]:
        """Format the conversation history for the LLM"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]
