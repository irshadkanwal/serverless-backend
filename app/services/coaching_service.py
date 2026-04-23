from datetime import datetime

from app.agents.coaching_agent import CoachingAgent
from app.agents.moderation_agent import ModerationAgent
from app.models.models import InitialMessageRequest, UserInput
from app.services.db.user_db_service import UserDataService
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.services.prompt_manager import PromptManager
from app.util.constants import DISPLAY_DATE_FORMAT
from app.util.helpers import format_iso_date_for_display, get_logger, handle_exceptions

logger = get_logger(__name__)


class CoachingService:
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.coaching_agent = CoachingAgent(llm_service, prompt_manager)
        self.moderate_agent = ModerationAgent(llm_service)
        self.user_service = UserDataService()
        self.prompts = PromptLoader()

    @handle_exceptions
    async def input_moderation(self, assistant_id: str, message: str) -> str | None:
        moderation_result = await self.moderate_agent.moderate_input_message(
            assistant_id, message
        )

        if not moderation_result.is_safe:
            return moderation_result.response

        return None

    @handle_exceptions
    async def handle_message(self, user_input: UserInput) -> tuple:
        """
        Handle a coaching interaction with output moderation and regeneration.
        """
        assistant_data = self.user_service.get_assistant_data(user_input)

        if assistant_data is None:
            return "Coach response generation failed. Please try again later.", None

        if assistant_data.llm_config is not None:
            self.coaching_agent.config_llm_service(assistant_data.llm_config)

        return await self._generate_with_moderation_retry(user_input, assistant_data)

    @handle_exceptions
    async def generate_initial_message(
        self, message_request: InitialMessageRequest
    ) -> str:
        """
        Generate an initial message for a conversation.
        This method generates a response using the coaching agent and moderates
        the output message.
        """
        assistant_data = self.user_service.get_assistant_data_by_id(
            message_request.assistant_id, message_request.recurring
        )

        if assistant_data is None:
            return "Initial message generation failed. Please try again later."

        if assistant_data.llm_config is not None:
            self.coaching_agent.config_llm_service(assistant_data.llm_config)

        initial_context = await self._build_initial_context(message_request)

        initial_message = await self.coaching_agent.generate_initial_message(
            assistant_data, message_request.user_name, initial_context
        )

        moderation_result = await self.moderate_agent.moderate_output_message(
            initial_message, message_request.assistant_id
        )

        if moderation_result.is_safe:
            return initial_message
        return "Assistant fails to respond on the message."

    async def _generate_with_moderation_retry(
        self, user_input: UserInput, assistant_data
    ) -> tuple:
        """
        Generate response with retry logic for output moderation failures.
        """
        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            coaching_response = await self.coaching_agent.generate_response(
                user_input, assistant_data
            )
            moderation_result = await self.moderate_agent.moderate_output_message(
                coaching_response, user_input.assistant_id
            )

            if moderation_result.is_safe:
                return coaching_response, assistant_data

            if attempt < max_attempts:
                continue

            failure_message = (
                await self.moderate_agent.service.generate_output_failure_response(
                    user_input.assistant_id
                )
            )
            return failure_message, None
        return None

    def _format_conversation_transcript(self, history: list[dict] | list) -> str:
        """Converts a list of Message objects or dicts to a formatted transcript."""
        if not history:
            return ""

        transcript_lines: list[str] = []
        for msg in history:
            role = msg.get("role") if isinstance(msg, dict) else msg.role
            content = msg.get("content") if isinstance(msg, dict) else msg.content
            created_at = (
                msg.get("created_at") if isinstance(msg, dict) else msg.created_at
            )
            timestamp = created_at.isoformat(timespec="seconds") if created_at else ""
            transcript_lines.append(f"[{timestamp}] {role.title()}: {content}")
        return "\n".join(transcript_lines)

    async def _build_initial_context(
        self, message_request: InitialMessageRequest
    ) -> str:
        """Builds the initial context string for a new conversation."""
        context_parts: list[str] = []

        today = datetime.now()
        formatted_date = today.strftime(DISPLAY_DATE_FORMAT)
        today_prompt = self.prompts.get_prompt("initial", "today-date-prompt")
        context_parts.append(today_prompt.render(current_date=formatted_date))

        if message_request.recurring:
            formatted_last_convo_date = format_iso_date_for_display(
                message_request.last_conversation_date
            )
            if formatted_last_convo_date:
                last_convo_prompt = self.prompts.get_prompt(
                    "initial", "last-conversation-date-prompt"
                )
                context_parts.append(
                    last_convo_prompt.render(
                        last_conversation_date=formatted_last_convo_date
                    )
                )

            if message_request.conversation_history:
                transcript_prompt = self.prompts.get_prompt(
                    "initial", "conversation-transcript-prompt"
                )
                transcript = self._format_conversation_transcript(
                    message_request.conversation_history
                )
                if transcript:
                    context_parts.append(
                        transcript_prompt.render(conversation_transcript=transcript)
                    )

        if message_request.language:
            context_parts.append(
                f"LANGUAGE: The user prefers responses in {message_request.language}."
            )

        return "\n\n".join(context_parts)
