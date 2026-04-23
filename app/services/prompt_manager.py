import re

from pydantic import BaseModel

from app.models.analyzer_model import StageDetail
from app.models.models import UserInput
from app.models.user_model import AICoachSetup
from app.services.db.file_db_service import FileDatabaseService
from app.services.db.user_db_service import UserDataService
from app.services.prompt_loader import PromptLoader
from app.services.reference_processor import EnhancedReference, ReferenceProcessor
from app.util.helpers import get_logger

logger = get_logger(__name__)


class PromptComponents(BaseModel):
    """Container for different components of a processed prompt"""

    main_content: str = ""
    remember_sections: list[str] = []
    stage_specific: str | None = None
    references: list[EnhancedReference] | None = None
    tone: str | None = None
    guidelines: str | None = None
    tone_examples: str | None = None
    missing_criteria: list[dict[str, str]] | None = None
    reasoning: str | None = None
    language: str | None = None


class PromptManager:
    def __init__(self):
        """Initialize the PromptManager with required services"""
        self.user_service = UserDataService()
        self.db_service = FileDatabaseService()
        self.reference_processor = ReferenceProcessor(self.db_service)
        self.prompts = PromptLoader()

    def _process_prompt_patterns(self, prompt: str) -> PromptComponents:
        """
        Extract REMEMBER sections from the prompt and return structured components.

        Args:
            prompt: The full prompt text containing potential REMEMBER sections

        Returns:
            PromptComponents: Container with main content and remember sections

        """
        if prompt is None:
            prompt = ""

        remember_pattern = r"REMEMBER[,:]?\s*(.*?)(?=REMEMBER[,:]?|$)"

        remember_matches = list(re.finditer(remember_pattern, prompt, re.DOTALL))
        remember_content = []

        for match in remember_matches:
            content = match.group(1).strip()
            if content:
                remember_content.append(content)

        main_content = prompt
        for match in reversed(remember_matches):
            start, end = match.span()
            main_content = (
                main_content[:start].strip() + " " + main_content[end:].strip()
            )

        main_content = re.sub(r"\s+", " ", main_content).strip()

        return PromptComponents(
            main_content=main_content, remember_sections=remember_content
        )

    def get_stage_prompt(self, assistant_id: str, stage: str) -> str:
        """
        Get stage-specific prompt from UserService.

        Args:
            assistant_id: The assistant's ID
            stage: The stage name

        Returns:
            Formatted stage-specific prompt

        """
        stage_data = self.user_service.get_stage_with_next(assistant_id, stage)

        if stage_data and stage_data.instructions:
            return (
                f"---Session Stage {stage_data.name} Guidelines---\\n\\n"
                f"{stage_data.instructions}"
            )
        return ""

    def get_analyzer_prompt(
        self, assistant_id: str, stage_name: str, assistant_data: AICoachSetup
    ) -> StageDetail:
        """
        Get analyzer prompt from UserService.

        Args:
            assistant_id: The assistant's ID
            stage_name: The stage name

        Returns:
            StageDetail object containing analyzer prompt

        """
        stage_data = self.user_service.get_stage_with_next(assistant_id, stage_name)

        # The case when coach onboard a new client
        if (
            assistant_data.stage
            and assistant_data.stage.is_first
            and not assistant_data.recurring
        ) and assistant_data.onboarding_analyzer is not None:
            stage_data.instructions = assistant_data.onboarding_analyzer

        return stage_data

    def get_user_prompt_components(
        self, assistant_details: AICoachSetup, input_details: UserInput | None = None
    ) -> PromptComponents:
        """
        Combine all prompt components in the correct order.

        Args:
            assistant_details: Assistant data containing instructions, stage

        Returns:
            PromptComponents: Structured prompt components

        """
        instructions = assistant_details.instructions

        components = self._process_prompt_patterns(instructions)
        components.tone = assistant_details.tone
        components.guidelines = assistant_details.guidelines
        components.tone_examples = assistant_details.tone_examples

        if input_details is not None:
            components.missing_criteria = input_details.missing_criteria
            components.reasoning = input_details.reasoning
            components.language = input_details.language

        if assistant_details.stage is not None:
            if assistant_details.stage.is_first:
                if (
                    not assistant_details.recurring
                    and assistant_details.onboarding is not None
                ):
                    stage = assistant_details.onboarding
                else:
                    stage = assistant_details.stage.instructions
                stage += (
                    "\n\n"
                    + self.prompts.get_prompt("initial", "recurring-note").render()
                    if assistant_details.recurring
                    else self.prompts.get_prompt("initial", "new-client-note").render()
                )
            else:
                stage = assistant_details.stage.instructions

            components.stage_specific = stage

        return components

    async def process_knowledge_references(
        self, components: PromptComponents
    ) -> PromptComponents:
        """
        Process knowledge references in the prompt components.

        Args:
            user_id: The user's ID
            components: The prompt components

        Returns:
            PromptComponents: Updated components with processed references

        """
        main_content, main_refs = self.reference_processor.process_references(
            components.main_content
        )

        stage_specific = components.stage_specific
        stage_refs = []
        if stage_specific:
            stage_specific, stage_refs = self.reference_processor.process_references(
                stage_specific
            )

        all_references = []
        ref_keys = set()

        for ref in main_refs + stage_refs:
            key = (
                ref.reference.document,
                ref.reference.type,
                ref.reference.section,
                ref.reference.pages,
            )
            if key not in ref_keys:
                ref_keys.add(key)
                all_references.append(ref)

        components.main_content = main_content
        components.stage_specific = stage_specific
        components.references = all_references

        return components

    def format_remember_sections(self, sections: list[str]) -> str:
        """
        Format REMEMBER sections consistently.

        Args:
            sections: List of REMEMBER section contents

        Returns:
            Formatted REMEMBER sections

        """
        return "\n\n".join(f"REMEMBER: {section.strip()}" for section in sections)

    async def format_coaching_prompt(
        self, components: PromptComponents, user_id: str
    ) -> tuple:
        """
        Format a complete coaching prompt with populated references.

        Args:
            components: Components to include in the prompt
            user_id: The user's ID for fetching reference content

        Returns:
            Formatted prompt messages for the LLM

        """
        coaching_response_instructions = self._build_coaching_response_instructions(
            components
        )
        messages = [
            {
                "role": "system",
                "content": f"# RESPONSE FORMAT:\n{coaching_response_instructions}",
            }
        ]

        if components.references:
            main_instructions = self.reference_processor.clean_remaining_references(
                components.main_content
            )
            stage_instructions = self.reference_processor.clean_remaining_references(
                components.stage_specific
            )
            stage_instructions = await self.reference_processor.populate_references(
                user_id, components.references, stage_instructions
            )
        else:
            main_instructions = components.main_content
            stage_instructions = components.stage_specific

        remember_content = None
        if components.remember_sections:
            remember_content = self.format_remember_sections(
                components.remember_sections
            )

        coaching_instructions = self._build_coaching_instructions(
            main_instructions, components, remember=remember_content
        )

        if components.stage_specific:
            messages.append(
                {
                    "role": "developer",
                    "content": f"# COACHING STAGE\n{stage_instructions}",
                }
            )

        if components.tone:
            messages.append(
                {"role": "system", "content": f"# TONE AND STYLE\n{components.tone}"}
            )

        if components.language:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"# LANGUAGE:\\nPrioritize answer in the user language "
                        f"{components.language}"
                    ),
                }
            )

        return messages, coaching_instructions

    def _build_coaching_instructions(
        self,
        main_instructions: str,
        components: PromptComponents,
        remember: str | None = None,
    ) -> str:
        """
        Build the coaching instructions for the LLM.
        """
        coaching_instructions = f"""
# COACHING PERSONA
{main_instructions}
"""

        # Always include the base ethical and safety guidelines
        ethical_guidelines = self.prompts.get_prompt(
            "coaching", "ethical-and-safety-guidelines"
        ).render()
        coaching_instructions += f"\n{ethical_guidelines}\n"

        # Append any additional, coach-specific guidelines
        if components.guidelines:
            coaching_instructions += (
                f"\n--- COACH-SPECIFIC GUIDELINES ---\n{components.guidelines}\n"
            )

        if remember:
            coaching_instructions += f"""
\n# REMEMBER
{remember}
"""

        return coaching_instructions

    def _build_coaching_response_instructions(
        self, components: PromptComponents
    ) -> str:
        """
        Build the coaching response instructions for the LLM.
        """
        reasoning_context = ""
        if components.reasoning:
            reasoning_prompt = self.prompts.get_prompt(
                "coaching", "reasoning-context-instructions"
            )
            reasoning_context = reasoning_prompt.render(reasoning=components.reasoning)

        missing_criteria_system_message = ""
        critical_missing_criteria_system_message = ""
        if components.missing_criteria:
            missing_prompt = self.prompts.get_prompt(
                "coaching", "missing-criteria-system-message"
            )
            missing_criteria_system_message = missing_prompt.render(
                missing_criteria=components.missing_criteria
            )
            critical_missing_criteria_system_message = self.prompts.get_prompt(
                "coaching", "critical-missing-criteria-system-message"
            ).render()

        response_instructions = self.prompts.get_prompt(
            "coaching", "coaching-response-instructions"
        )
        function_call_prompt = self.prompts.get_prompt(
            "coaching", "function-call-instructions"
        )

        return response_instructions.render(
            reasoning_context=reasoning_context,
            missing_criteria_system_message=missing_criteria_system_message,
            critical_missing_criteria_system_message=critical_missing_criteria_system_message,
            function_call_instructions=function_call_prompt.render(),
        )
