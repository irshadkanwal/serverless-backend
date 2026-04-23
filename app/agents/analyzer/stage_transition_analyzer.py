from app.agents.analyzer.base_analyzer import BaseAnalyzer
from app.models.analyzer_model import (
    STAGE_TRANSITION_INDICATORS,
    AnalysisRequest,
    StageDetail,
    StageTransitionResult,
)
from app.models.models import UserInput
from app.models.user_model import AICoachSetup
from app.services.db.user_db_service import UserDataService
from app.services.llm.llm_service import LLMService
from app.services.notification_service import NotificationService
from app.services.prompt_loader import PromptLoader
from app.services.prompt_manager import PromptManager
from app.util.helpers import get_logger, handle_exceptions

logger = get_logger(__name__)


class StageTransitionAnalyzer(BaseAnalyzer[StageTransitionResult]):
    """Analyzer specifically for stage transitions"""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.notification_service = NotificationService()
        self.user_service = UserDataService()
        self.prompts = PromptLoader()

    async def analyze(
        self,
        user_input: UserInput,
        assistant_response: str,
        assistant_data: AICoachSetup | None = None,
    ):
        """
        Analyze if stage transition is needed, with support for flexible stage
        progression
        """
        if not assistant_data or not assistant_data.stage:
            logger.error(
                "Assistant data or stage is None, cannot perform stage "
                "transition analysis"
            )
            return

        request = None
        stages = []

        try:
            request = self._build_analysis_request(
                user_input, assistant_response, assistant_data.stage.name
            )
            llm_request, stages, stage_data = self._build_stage_transition_prompt(
                request, assistant_data, user_input.missing_criteria
            )

            try:
                analysis: StageTransitionResult = (
                    await self.llm_service.system_task_processing(
                        llm_request, StageTransitionResult
                    )
                )

                if analysis.transition_required:
                    analysis = self._process_transition_analysis(
                        request, analysis, stages, stage_data
                    )

                await self._send_stage_transition_notification(
                    analysis, user_input, stages[0] if stages else None
                )
            except Exception as e:
                logger.error(f"Error in conversation analysis notification: {e!s}")
                if request:
                    await self._send_stage_transition_notification(
                        self._build_empty_response(request.current_stage),
                        user_input,
                        stages[0] if stages else None,
                    )
        except Exception as e:
            logger.error(f"Error in conversation analysis request: {e!s}")
            if request:
                await self._send_stage_transition_notification(
                    self._build_empty_response(request.current_stage),
                    user_input,
                    stages[0] if stages else None,
                )

    def _build_stage_transition_prompt(
        self,
        request: AnalysisRequest,
        assistant_data: AICoachSetup,
        missing_criteria: list[str],
    ) -> tuple:
        """Build the prompt for stage transition analysis"""
        assistant_id = (
            request.metadata.get("assistant_id") if request.metadata else None
        )
        missing_criteria_context = ""
        stage_data = self.prompt_manager.get_analyzer_prompt(
            assistant_id,
            request.current_stage,
            assistant_data,
        )

        stages = self.user_service.get_stage_sequence(assistant_id) or []
        all_stages = "\n".join(f"- {s}" for s in stages)

        session_history = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in request.session_history
        )

        stage_history = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in request.stage_history
        )

        analyzer_content = stage_data.analyzer or ""
        has_evaluation_criteria = (
            "evaluate" in analyzer_content.lower()
            or "criteria" in analyzer_content.lower()
        )
        has_transition_criteria = "transition" in analyzer_content.lower() and any(
            word in analyzer_content.lower()
            for word in ["criteria", "requirements", "conditions"]
        )

        if not has_evaluation_criteria:
            analyzer_content += self.prompts.get_prompt(
                "analysis", "stage-evaluation-criteria"
            ).render()
        if not has_transition_criteria:
            analyzer_content += self.prompts.get_prompt(
                "analysis", "stage-transition-criteria"
            ).render()

        if missing_criteria and len(missing_criteria) > 0:
            missing_criteria_context = self.prompts.get_prompt(
                "analysis", "stage-missing-criteria-system-message"
            ).render(missing_criteria=missing_criteria)

        system_message = [
            {
                "role": "system",
                "content": self.prompts.get_prompt(
                    "analysis", "stage-transition-system-message"
                ).render(
                    current_stage=stage_data.name,
                    all_stages=all_stages,
                    session_history=session_history,
                    stage_history=stage_history,
                    analysis_context=analyzer_content,
                    missing_criteria=missing_criteria_context,
                ),
            }
        ]

        system_message.append(
            {
                "role": "developer",
                "content": self.prompts.get_prompt(
                    "analysis", "stage-decision-making-prompt"
                ).render(),
            }
        )

        return system_message, stages, stage_data

    def _build_analysis_request(
        self, user_input: UserInput, assistant_response: str, current_stage: str
    ) -> AnalysisRequest:
        """Build the analysis request for the LLM"""
        current_stage_history = [
            {"role": msg.role, "content": msg.content}
            for msg in user_input.history
            if msg.stage == current_stage
        ]
        current_stage_history.append(
            {
                "role": user_input.newMessage.role,
                "content": user_input.newMessage.content,
            }
        )
        current_stage_history.append(
            {"role": "assistant", "content": assistant_response}
        )

        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in user_input.history
            if msg.stage != current_stage
        ]

        return AnalysisRequest(
            session_history=conversation_history,
            stage_history=current_stage_history,
            current_stage=current_stage,
            metadata={"assistant_id": user_input.assistant_id},
        )

    def _build_empty_response(self, current_stage: str) -> StageTransitionResult:
        """Build an empty response for the analyzer"""
        return StageTransitionResult(
            transition_required=False,
            current_stage=current_stage,
            next_stage=None,
            confidence=0.0,
            reasoning="Unable to analyze conversation progression.",
            criteria_missing=[],
            transition_direction="none",
            return_indicators={},
        )

    def _extract_stage_keywords(self, stages: list) -> dict:
        """Extract keywords from stage names for better analysis"""
        stage_keywords = {}
        for stage in stages:
            words = stage.replace("_", " ").split()
            keywords = [
                w
                for w in words
                if len(w) > 3
                and w not in ("check", "get", "if", "to", "for", "the", "and", "stage")
            ]
            stage_keywords[stage] = keywords
        return stage_keywords

    def _process_transition_analysis(
        self,
        request: AnalysisRequest,
        analysis: StageTransitionResult,
        stages: list[str],
        stage_data: StageDetail,
    ) -> StageTransitionResult:
        """
        Process the transition analysis results to determine if stages should be
        skipped.

        This method analyzes user input and LLM reasoning to detect when multiple stages
        can be bypassed in a single transition.

        Args:
            request: The original analysis request containing conversation history
            analysis: The initial transition analysis result from the LLM
            stages: The sequence of available stages
            stage_data: Details about the current stage

        Returns:
            Updated StageTransitionResult with potentially modified next_stage

        """
        current_index = (
            stages.index(stage_data.name) if stage_data.name in stages else -1
        )
        next_index = (
            stages.index(analysis.next_stage)
            if analysis.next_stage and analysis.next_stage in stages
            else -1
        )

        if current_index < 0 or next_index <= current_index:
            return analysis

        user_input_text = " ".join(
            [
                m.get("content", "").lower()
                for m in request.stage_history
                if m.get("role") == "user"
            ]
        )

        reasoning = analysis.reasoning.lower()
        is_skip_indicator = any(
            keyword in analysis.reasoning.lower()
            for keyword in STAGE_TRANSITION_INDICATORS
        )

        max_look_ahead = min(2, len(stages) - current_index)
        stage_keywords = self._extract_stage_keywords(stages)

        furthest_stage, furthest_index = self._find_furthest_addressed_stage(
            current_index,
            max_look_ahead,
            stages,
            user_input_text,
            stage_keywords,
            analysis.reasoning.lower(),
        )

        if is_skip_indicator and next_index + 1 < len(stages):
            for look_ahead in range(2, min(4, len(stages) - current_index)):
                target_index = current_index + look_ahead

                if target_index < len(stages):
                    target_stage = stages[target_index]
                    stage_terms = target_stage.lower().replace("_", " ").split()

                    transition_terms = [term for term in stage_terms if len(term) > 3]

                    if any(term in reasoning for term in transition_terms):
                        analysis = self._update_analysis(analysis, target_stage)
                        break
        elif furthest_stage and furthest_index > next_index:
            analysis = self._update_analysis(analysis, furthest_stage)

        return analysis

    def _find_furthest_addressed_stage(
        self,
        current_index: int,
        max_look_ahead: int,
        stages: list[str],
        user_input_text: str,
        stage_keywords: dict,
        reasoning_text: str,
    ) -> tuple[str | None, int]:
        """
        Find the furthest stage that appears to be addressed in the conversation.

        Args:
            current_index: Index of the current stage
            max_look_ahead: Maximum number of stages to look ahead
            stages: List of all stages
            user_input_text: Lowercase user input for matching
            stage_keywords: Dictionary mapping stage names to their keywords
            reasoning_text: Lowercase reasoning text from the LLM

        Returns:
            Tuple of (furthest_stage_name, furthest_stage_index) or
            (None, current_index)

        """
        furthest_stage = None
        furthest_index = current_index

        for i in range(current_index + 1, current_index + max_look_ahead):
            if i >= len(stages):
                break

            stage_name = stages[i]
            normalized_stage = stage_name.lower().replace("_", " ")

            if (
                normalized_stage in user_input_text
                or any(
                    kw in user_input_text for kw in stage_keywords.get(stage_name, [])
                )
                or normalized_stage in reasoning_text
            ):
                furthest_stage = stage_name
                furthest_index = i

        return furthest_stage, furthest_index

    def _update_analysis(
        self, analysis: StageTransitionResult, next_stage: str
    ) -> StageTransitionResult:
        """
        Update the analysis result with the new stage and reasoning.

        Args:
            analysis: The original analysis result
            next_stage: The stage to transition to

        Returns:
            Updated StageTransitionResult

        """
        analysis.next_stage = next_stage
        analysis.criteria_missing = []
        return analysis

    @handle_exceptions
    async def _send_stage_transition_notification(
        self,
        analysis: StageTransitionResult,
        user_input: UserInput,
        initial_stage: str | None = None,
    ):
        """
        Send a notification about the stage transition.

        Args:
            analysis: The analysis result containing transition details

        """
        await self.notification_service.notify_stage_transition(
            analysis,
            user_input,
            initial_stage,
        )
