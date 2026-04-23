import json

from app.agents.base_agent import BaseAgent
from app.models.summary_models import SessionSummaryContent
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.util.helpers import handle_exceptions


class SessionSummaryAgent(BaseAgent[SessionSummaryContent, str]):
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompts = PromptLoader()

    @handle_exceptions
    def process(self, request: SessionSummaryContent) -> str:
        session_prompt = self.prompts.get_prompt(
            "summary", "session-summary-system-message"
        )
        context = [{"role": "system", "content": session_prompt.render()}]

        context.extend(
            [
                {"role": "system", "content": f"Stage Summary: {json.dumps(summary)}"}
                for summary in request.stage_summaries
            ]
        )

        return self.llm_service.generate_json_response(context)
