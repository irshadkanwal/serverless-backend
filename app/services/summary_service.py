from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.util.helpers import get_logger

logger = get_logger(__name__)


class SummaryService:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.prompts = PromptLoader()

    def session_context(self, summary: dict, current_stage: str) -> str:
        """
        Format the previous stage summary into useful context for the current stage
        """
        try:
            stage_specific = summary.get("stage_specific", {})
            stage_specific_info = "\n".join(
                f"- {key}: {value}" for key, value in stage_specific.items() if value
            )

            session_context_prompt = self.prompts.get_prompt(
                "summary", "session-context-system-message"
            )
            return session_context_prompt.render(
                previous_stage=summary.get("stage", "Unknown"),
                emotional_state=summary.get("emotional_state", "Unknown"),
                key_points="\n  * "
                + "\n  * ".join(summary.get("key_points", ["No key points recorded"])),
                insights="\n  * "
                + "\n  * ".join(summary.get("insights", ["No insights recorded"])),
                progress_indicators="\n  * "
                + "\n  * ".join(
                    summary.get(
                        "progress_indicators", ["No progress indicators recorded"]
                    )
                ),
                stage_specific_info=stage_specific_info,
                # @TODO: need to add some specifics key insights from the stage
                # instructions and analysis
                current_stage=current_stage,
                recommendations="\n  * "
                + "\n  * ".join(
                    summary.get(
                        "next_stage_recommendations", ["No specific recommendations"]
                    )
                ),
            )

        except Exception as e:
            logger.error(f"Error formatting summary context: {e!s}")

        return ""
