from unittest.mock import Mock, patch

import pytest

from app.models.models import Message, UserInput
from app.models.user_model import AICoachSetup, StageData
from app.services.prompt_manager import PromptComponents, PromptManager


class TestPromptManager:
    @pytest.fixture
    def prompt_manager(self):
        with (
            patch("app.services.prompt_manager.UserDataService"),
            patch("app.services.prompt_manager.FileDatabaseService"),
            patch("app.services.prompt_manager.ReferenceProcessor"),
        ):
            return PromptManager()

    def test_process_prompt_patterns_with_remember_sections(self, prompt_manager):
        prompt = "Main instructions REMEMBER: important fact REMEMBER: another fact"

        result = prompt_manager._process_prompt_patterns(prompt)

        assert result.main_content == "Main instructions"
        assert len(result.remember_sections) == 2
        assert "important fact" in result.remember_sections
        assert "another fact" in result.remember_sections

    def test_process_prompt_patterns_no_remember_sections(self, prompt_manager):
        prompt = "Just main instructions without any special sections"

        result = prompt_manager._process_prompt_patterns(prompt)

        assert (
            result.main_content == "Just main instructions without any special sections"
        )
        assert len(result.remember_sections) == 0

    def test_process_prompt_patterns_empty_prompt(self, prompt_manager):
        result = prompt_manager._process_prompt_patterns("")

        assert result.main_content == ""
        assert len(result.remember_sections) == 0

    def test_format_remember_sections(self, prompt_manager):
        sections = ["First important thing", "Second important thing"]

        result = prompt_manager.format_remember_sections(sections)

        assert "REMEMBER: First important thing" in result
        assert "REMEMBER: Second important thing" in result

    def test_get_user_prompt_components_basic(self, prompt_manager):
        assistant_details = AICoachSetup(
            userId="user123",
            assistantConfigurationId="config123",
            instructions="Be helpful",
            tone="friendly",
            guidelines="Be safe",
        )

        result = prompt_manager.get_user_prompt_components(assistant_details)

        assert result.main_content == "Be helpful"
        assert result.tone == "friendly"
        assert result.guidelines == "Be safe"

    def test_get_user_prompt_components_with_stage(self, prompt_manager):
        stage = StageData(
            name="intro",
            instructions="Introduction stage",
            analyzer="analyze this",
            is_first=True,
        )
        assistant_details = AICoachSetup(
            userId="user123",
            assistantConfigurationId="config123",
            instructions="Be helpful",
            stage=stage,
            recurring=False,
        )

        result = prompt_manager.get_user_prompt_components(assistant_details)

        assert result.main_content == "Be helpful"
        assert "Introduction stage" in result.stage_specific
        assert "new client" in result.stage_specific.lower()

    def test_get_user_prompt_components_with_input_details(self, prompt_manager):
        assistant_details = AICoachSetup(
            userId="user123",
            assistantConfigurationId="config123",
            instructions="Be helpful",
        )
        input_details = UserInput(
            assistant_id="asst123",
            user_id="user123",
            history=[],
            newMessage=Message(role="user", content="Hello"),
            language="Spanish",
            reasoning="User wants greeting",
        )

        result = prompt_manager.get_user_prompt_components(
            assistant_details, input_details
        )

        assert result.language == "Spanish"
        assert result.reasoning == "User wants greeting"

    async def test_process_knowledge_references(self, prompt_manager):
        components = PromptComponents(
            main_content="Use knowledge from [doc:manual]",
            stage_specific="Follow [doc:guide] for this stage",
        )

        # Mock the reference processor
        prompt_manager.reference_processor.process_references = Mock(
            side_effect=[
                ("Use knowledge from processed", [Mock()]),
                ("Follow processed for this stage", [Mock()]),
            ]
        )

        result = await prompt_manager.process_knowledge_references(components)

        assert result.main_content == "Use knowledge from processed"
        assert result.stage_specific == "Follow processed for this stage"
        assert len(result.references) == 2
