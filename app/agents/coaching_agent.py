from datetime import datetime

from app.models.coaching_model import AssistantResponse
from app.models.coaching_request_model import CoachingRequest
from app.models.llm_config_model import LLMConfig
from app.models.models import UserInput
from app.models.user_model import AICoachSetup
from app.services.db.user_db_service import UserDataService
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.services.prompt_manager import PromptComponents, PromptManager
from app.util.constants import MESSAGE_DATE_FORMAT
from app.util.helpers import get_logger, handle_exceptions


class CoachingAgent:
    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.user_service = UserDataService()
        self.prompt_manager = prompt_manager
        self.logger = get_logger(__name__)
        self.prompts = PromptLoader()

    @handle_exceptions
    async def generate_response(
        self,
        input_details: UserInput,
        assistant_data: AICoachSetup,
    ) -> str:
        """Main entrypoint: choose prompt and route to plain or knowledge flows."""
        response = await self.process_user_request(input_details, assistant_data)

        if response is None:
            self.logger.error("Failed to generate a response due to an internal error.")
            return (
                "I'm sorry, but I encountered an error and can't respond right now. "
                "Please try again later."
            )

        return response.get_formatted_response()

    @handle_exceptions
    async def process_user_request(
        self,
        input_details: UserInput,
        assistant_data: AICoachSetup,
    ) -> AssistantResponse:
        """Process user request and return response."""
        history_content = []
        for msg in input_details.history:
            content = msg.content
            if msg.created_at:
                formatted_date = msg.created_at.strftime(MESSAGE_DATE_FORMAT)
                content = formatted_date + content
            history_content.append({"role": msg.role, "content": content})

        current_date_str = datetime.now().strftime(MESSAGE_DATE_FORMAT)
        new_message_content = current_date_str + input_details.newMessage.content
        history_content.append({"role": "user", "content": new_message_content})

        comps = self.prompt_manager.get_user_prompt_components(
            assistant_data, input_details
        )

        return await self._coaching_response(
            assistant_data, comps, history_content, input_details
        )

    def config_llm_service(self, llm_config: LLMConfig):
        """Update LLM service configuration."""
        self.llm_service.config = llm_config

    @handle_exceptions
    async def generate_initial_message(
        self,
        assistant_data: AICoachSetup,
        user_name: str,
        initial_context: str | None = None,
    ) -> str:
        """Generate an initial message for a conversation."""
        comps = self.prompt_manager.get_user_prompt_components(assistant_data)

        if user_name is not None:
            user_name_note = self.prompts.get_prompt(
                "initial", "user-name-note"
            ).render(user_name=user_name)
            comps.stage_specific += f"\n{user_name_note}"

        if initial_context:
            comps.stage_specific = f"{initial_context}\n\n{comps.stage_specific}"

        initial_message = await self._coaching_response(
            assistant_data, comps, None, None
        )

        if not initial_message:
            return "Assistant fails to respond on the message."

        return initial_message.get_formatted_response()

    ### Private methods ###

    @handle_exceptions
    async def _coaching_response(
        self,
        assistant_data: AICoachSetup,
        prompt_components: PromptComponents,
        history_content: list[dict[str, str]] | None,
        input_details: UserInput | None = None,
    ) -> AssistantResponse:
        (
            llm_messages,
            coaching_instructions,
        ) = await self.prompt_manager.format_coaching_prompt(
            prompt_components, assistant_data.userId
        )

        if history_content is not None:
            llm_messages.extend(history_content)

        coachee_id = input_details.user_id if input_details else ""

        is_initial_message = history_content is None

        request = CoachingRequest(
            messages=llm_messages,
            instructions=coaching_instructions,
            user_id=coachee_id,
            tone_examples=prompt_components.tone_examples,
            workspace=assistant_data.userId,
            knowledge_ids=assistant_data.knowledge_ids,
            is_initial_message=is_initial_message,
        )

        return await self.llm_service.generate_coaching_response(request)
