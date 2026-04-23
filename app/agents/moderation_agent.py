from app.models.moderation_model import ModerationResult, ModerationRule, ModerationType
from app.services.db.user_db_service import UserDataService
from app.services.llm.llm_service import LLMService
from app.services.moderation_service import ModerationService
from app.util.helpers import handle_exceptions


class ModerationAgent:
    def __init__(self, llm_service: LLMService):
        user_service = UserDataService()
        self.llm_service = llm_service
        self.service = ModerationService(user_service, llm_service)

    @handle_exceptions
    async def moderate_input_message(
        self, assistant_id: str, message: str, language: str = "en"
    ) -> ModerationResult:
        """
        Check message content and return either safe status or moderation response.
        Single entry point that handles the full moderation cycle.
        """
        moderation_rules = self.service.moderation_rules(assistant_id)

        return await self._execute_default_moderation(
            message, moderation_rules, ModerationType.INPUT, language
        )

    @handle_exceptions
    async def moderate_output_message(
        self, message: str, assistant_id: str, language: str = "en"
    ) -> ModerationResult:
        """
        Check message content and return either safe status or moderation response.
        Single entry point that handles the full moderation cycle.
        """
        moderation_rules = self.service.moderation_rules(assistant_id)

        return await self._execute_default_moderation(
            message, moderation_rules, ModerationType.OUTPUT, language
        )

    @handle_exceptions
    async def _execute_default_moderation(
        self,
        message: str,
        moderation_rules: list[ModerationRule],
        type: ModerationType,
        language,
    ) -> ModerationResult:
        """Execute default moderation rules"""
        moderation_result = await self.llm_service.moderate_message(message)

        if not moderation_result.flagged:
            return ModerationResult(is_safe=True)

        score_field = "input_score" if type == ModerationType.INPUT else "output_score"
        allowed_categories = {
            rule.allow_category: getattr(rule, score_field)
            for rule in moderation_rules
            if rule.allow_category and getattr(rule, score_field) is not None
        }

        flagged_categories = moderation_result.categories.model_dump(by_alias=True)
        category_scores = moderation_result.category_scores.model_dump(by_alias=True)

        for category, flagged in flagged_categories.items():
            if flagged:
                if (
                    category in allowed_categories
                    and category_scores[category] < allowed_categories[category]
                ):
                    continue

                if type == ModerationType.INPUT:
                    response = await self.service.generate_template_response(
                        moderation_rules, category, language, message
                    )
                    return ModerationResult(is_safe=False, response=response)
                if type == ModerationType.OUTPUT:
                    return ModerationResult(is_safe=False)

        return ModerationResult(is_safe=True)

    async def _execute_custom_moderation(
        self, message: str, rules: list[ModerationRule]
    ) -> ModerationResult:
        """
        Evaluates message against user's moderation rules using LLM.

        Args:
            message: Message to moderate
            llm_service: LLM service instance

        Returns:
            ModerationResult with responses

        """
        try:
            prompt = self.service.build_moderation_prompt(rules, message)
            return await self.llm_service.system_task_processing(
                prompt, ModerationResult
            )

        except Exception as _:
            return ModerationResult(
                is_safe=True,
                response=(
                    "We're unable to process your message as it contains content that "
                    "may not align with our guidelines. Could you please rephrase it?"
                ),
            )
