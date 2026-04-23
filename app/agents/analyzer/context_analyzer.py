from app.agents.analyzer.base_analyzer import BaseAnalyzer
from app.models.analyzer_model import AnalysisRequest, ContextNeedResult
from app.services.context_manager import CoachingContextManager
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.services.prompt_manager import PromptManager
from app.util.helpers import get_logger

logger = get_logger(__name__)


class ContextNeedAnalyzer(BaseAnalyzer[ContextNeedResult]):
    """Analyzer for determining when historical context is needed"""

    def __init__(
        self,
        llm_service: LLMService,
        prompt_manager: PromptManager,
        context_manager: CoachingContextManager,
    ):
        self.prompts = PromptLoader()
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.context_manager = context_manager

    async def analyze(self, request: AnalysisRequest) -> ContextNeedResult:
        system_message = {
            "role": "system",
            "content": self.prompts.get_prompt(
                "analysis", "context-need-system-message"
            ).render(conversation_history=request.stage_history),
        }

        result = await self.llm_service.generate_json_response([system_message])
        context_need = ContextNeedResult.model_validate_json(result)

        if context_need.context_required and context_need.context_priority in [
            "high",
            "medium",
        ]:
            relevant_context = await self._fetch_relevant_context(
                request.metadata.get("assistant_id") if request.metadata else None,
                request.metadata.get("chat_id") if request.metadata else None,
                context_need.topics_for_context,
            )

            if relevant_context and request.metadata:
                request.metadata["relevant_context"] = relevant_context
                context_need.relevance_score = self._calculate_context_relevance(
                    context_need.topics_for_context, relevant_context
                )

        return context_need

    async def _fetch_relevant_context(
        self, assistant_id: str, chat_id: str, topics: list[str]
    ) -> dict:
        """Fetch relevant context using CoachingContextManager"""
        try:
            context = await self.context_manager.find_relevant_context(
                chat_id=chat_id, assistant_id_id=assistant_id
            )

            return {
                "related_insights": self._filter_by_topics(
                    context.get("related_insights", []), topics
                ),
                "relevant_actions": self._filter_by_topics(
                    context.get("relevant_actions", []), topics
                ),
                "previous_progress": self._filter_by_topics(
                    context.get("previous_progress", []), topics
                ),
            }

        except Exception as e:
            logger.error(f"Error fetching context: {e!s}")
            return {}

    def _filter_by_topics(
        self, context_items: list[dict], topics: list[str]
    ) -> list[dict]:
        """Filter context items by relevance to requested topics"""
        relevant_items = []

        for item in context_items:
            relevance = sum(
                1 for topic in topics if topic.lower() in str(item).lower()
            ) / len(topics)

            if relevance > 0.3:
                item["relevance_score"] = relevance
                relevant_items.append(item)

        return sorted(relevant_items, key=lambda x: x["relevance_score"], reverse=True)

    def _calculate_context_relevance(
        self, requested_topics: list[str], found_context: dict
    ) -> float:
        """Calculate overall relevance score of found context"""
        if not found_context or not requested_topics:
            return 0.0

        topics_with_context = set()

        for context_list in found_context.values():
            for item in context_list:
                for topic in requested_topics:
                    if topic.lower() in str(item).lower():
                        topics_with_context.add(topic)

        return len(topics_with_context) / len(requested_topics)
