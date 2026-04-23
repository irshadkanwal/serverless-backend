from app.services.db.user_db_service import UserDataService
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.util.helpers import get_logger, handle_exceptions

logger = get_logger(__name__)


class ModerationService:
    def __init__(self, user_service: UserDataService, llm_service: LLMService):
        self.user_service = user_service
        self.llm_service = llm_service
        self.prompts = PromptLoader()

    @handle_exceptions
    def moderation_rules(self, assistant_id: str) -> list | None:
        """
        Fetch moderation rules for a specific assistant.
        """
        if not assistant_id:
            return None

        return self.user_service.get_user_moderation(assistant_id)

    @handle_exceptions
    async def generate_template_response(
        self,
        moderation_rules: list,
        flagged_category: str,
        language: str,
        original_message: str,
    ) -> str:
        """Generate response using templates or fallback to default response."""
        matching_rule = next(
            (
                rule
                for rule in moderation_rules
                if rule.allow_category == flagged_category
            ),
            None,
        )

        if matching_rule and matching_rule.response_examples:
            messages = [
                {
                    "role": "system",
                    "content": self.prompts.get_prompt(
                        "moderation", "template-moderation-system-message"
                    ).render(
                        flagged_category=flagged_category,
                        response_examples=matching_rule.response_examples,
                        language=language,
                    ),
                },
                {
                    "role": "user",
                    "content": f"Original flagged message: '{original_message}'",
                },
            ]

            try:
                return await self.llm_service.generate_response(messages)
            except Exception as e:
                logger.error(f"Template response generation error: {e!s}")

        return await self.generate_default_response(flagged_category, language)

    @handle_exceptions
    async def generate_default_response(
        self, flagged_category: str, language: str
    ) -> str:
        """
        Generate an appropriate response for content that has been flagged by
        moderation rules.
        """
        category_display = flagged_category.replace("_", " ").replace("/", " - ")
        user_message = self.prompts.get_prompt(
            "moderation", "default-moderation-user-message"
        ).render()

        messages = [
            {
                "role": "system",
                "content": self.prompts.get_prompt(
                    "moderation", "default-moderation-system-message"
                ).render(),
            },
            {
                "role": "user",
                "content": (
                    f"{user_message} {category_display}. "
                    f"Respond in {language} language."
                ),
            },
        ]

        try:
            return await self.llm_service.generate_response(messages)
        except Exception as e:
            logger.error(f"Response generation error: {e!s}")
            return self.prompts.get_prompt(
                "moderation", "default-input-moderation-fallback"
            ).render()

    @handle_exceptions
    async def generate_output_failure_response(self, assistant_id: str) -> str:
        """
        Generate user-facing message when AI coach response fails moderation
        after retries. Uses templates if available, otherwise returns default
        message.
        """
        moderation_rules = self.moderation_rules(assistant_id)

        for rule in moderation_rules:
            if rule.response_examples:
                try:
                    messages = [
                        {
                            "role": "system",
                            "content": self.prompts.get_prompt(
                                "moderation", "output-failure-system-message"
                            ).render(response_examples=rule.response_examples),
                        },
                        {
                            "role": "user",
                            "content": self.prompts.get_prompt(
                                "moderation", "output-failure-user-message"
                            ).render(),
                        },
                    ]

                    return await self.llm_service.generate_response(messages)
                except Exception as e:
                    logger.error(f"Template failure message generation error: {e!s}")
                    break

        return self.prompts.get_prompt(
            "moderation", "default-output-failure-fallback"
        ).render()
