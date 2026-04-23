from app.agents.analyzer.base_analyzer import BaseAnalyzer
from app.models.analyzer_model import AnalysisRequest, ContentAnalysisResult
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.services.prompt_manager import PromptManager


class ContentAnalyzer(BaseAnalyzer[ContentAnalysisResult]):
    """Combined analyzer for topics and life areas"""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.prompts = PromptLoader()

    async def analyze(self, request: AnalysisRequest) -> ContentAnalysisResult:
        previous_content = self._format_previous_content(
            request.metadata.get("previous_content_analysis")
            if request.metadata
            else None
        )

        system_message = {
            "role": "system",
            "content": self.prompts.get_prompt(
                "analysis", "content-analysis-system-message"
            ).render(
                previous_content=previous_content,
                conversation_history=request.session_history,
            ),
        }

        result = await self.llm_service.generate_json_response([system_message])
        return ContentAnalysisResult.model_validate_json(result)

    def _format_previous_content(self, previous: dict | None) -> str:
        """Format previous content analysis for the prompt"""
        if not previous:
            return "No previous content analysis available."

        formatted = "Previous analysis summary:\n"

        formatted += "\nActive Topics:\n"
        for topic in previous.get("topics", []):
            formatted += f"- {topic['name']} (confidence: {topic['confidence']:.2f})\n"
            formatted += f"  Key points: {', '.join(topic['key_points'])}\n"

        formatted += "\nLife Areas Focus:\n"
        for area in previous.get("life_areas", []):
            formatted += (
                f"- {area['area']} (relevance: {area['relevance']:.2f}), "
                f"trend: {area.get('trend', 'stable')}\n"
            )

        formatted += (
            f"\nPrevious primary focus: "
            f"{previous.get('primary_focus', 'None identified')}\n"
        )

        return formatted
