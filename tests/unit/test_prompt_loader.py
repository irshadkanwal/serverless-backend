"""
Unit tests for the PromptLoader system.

Tests the core functionality of loading prompts from markdown files,
caching, formatting, and backwards compatibility.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.services.prompt_loader import (
    Prompt,
    PromptLoader,
    PromptMetadata,
    _load_prompt,
    get_prompt,
    get_prompt_loader,
    render_prompt,
)


class TestPromptLoader:
    """Test suite for PromptLoader class"""

    @pytest.fixture
    def temp_prompts_dir(self):
        """Create a temporary directory with test prompts"""
        temp_dir = Path(tempfile.mkdtemp())

        # Create test structure
        coaching_dir = temp_dir / "coaching"
        coaching_dir.mkdir()

        # Create a test prompt file
        test_prompt = coaching_dir / "test-prompt.md"
        test_prompt.write_text("""---
name: "TEST_PROMPT"
description: "Test prompt for testing"
category: "coaching"
source_file: "test_prompts"
---
This is a test prompt with {variable} placeholder.""")

        # Create another test prompt
        another_prompt = coaching_dir / "another-prompt.md"
        another_prompt.write_text("""---
name: "ANOTHER_PROMPT"
description: "Another test prompt"
category: "coaching"
source_file: "test_prompts"
---
Simple prompt without variables.""")

        # Create a prompt in another category
        analysis_dir = temp_dir / "analysis"
        analysis_dir.mkdir()

        analysis_prompt = analysis_dir / "analysis-prompt.md"
        analysis_prompt.write_text("""---
name: "ANALYSIS_PROMPT"
description: "Analysis test prompt"
category: "analysis"
source_file: "analysis_prompts"
---
Analysis with {param1} and {param2}.""")

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def prompt_loader(self, temp_prompts_dir):
        """Create a PromptLoader with test directory"""
        return PromptLoader(prompts_dir=temp_prompts_dir)

    def test_init_with_default_path(self):
        """Test PromptLoader initialization with default path"""
        with patch.object(Path, "exists", return_value=True):
            loader = PromptLoader()
            assert loader.prompts_dir.name == "prompts_md"

    def test_get_prompt_success(self, prompt_loader):
        """Test successful prompt loading"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")

        assert isinstance(prompt, Prompt)
        assert prompt.metadata.name == "TEST_PROMPT"
        assert prompt.metadata.description == "Test prompt for testing"
        assert prompt.metadata.category == "coaching"
        assert "test prompt with test" in prompt.render(variable="test")

    def test_get_prompt_not_found(self, prompt_loader):
        """Test handling of non-existent prompt"""
        with pytest.raises(FileNotFoundError, match="Prompt not found"):
            prompt_loader.get_prompt("coaching", "non-existent")

    def test_prompt_format(self, prompt_loader):
        """Test prompt formatting with variables"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")
        formatted = prompt.render(variable="VALUE")

        assert "This is a test prompt with VALUE placeholder" in formatted
        assert "{variable}" not in formatted

    def test_prompt_format_multiple_variables(self, prompt_loader):
        """Test formatting with multiple variables"""
        prompt = prompt_loader.get_prompt("analysis", "analysis-prompt")
        formatted = prompt.render(param1="first", param2="second")

        assert "Analysis with first and second" in formatted

    def test_list_categories(self, prompt_loader):
        """Test listing available categories"""
        categories = prompt_loader.list_categories()

        assert "coaching" in categories
        assert "analysis" in categories
        assert len(categories) == 2

    def test_list_prompts_in_category(self, prompt_loader):
        """Test listing prompts in a category"""
        prompts = prompt_loader.list_prompts("coaching")

        assert "test-prompt" in prompts
        assert "another-prompt" in prompts
        assert len(prompts) == 2

    def test_list_prompts_empty_category(self, prompt_loader):
        """Test listing prompts in non-existent category"""
        prompts = prompt_loader.list_prompts("non-existent")
        assert prompts == []

    def test_get_category(self, prompt_loader):
        """Test loading all prompts from a category"""
        coaching_prompts = prompt_loader.get_category("coaching")

        assert "test-prompt" in coaching_prompts
        assert "another-prompt" in coaching_prompts
        assert isinstance(coaching_prompts["test-prompt"], Prompt)

    def test_search_prompts_by_name(self, prompt_loader):
        """Test searching prompts by name"""
        results = prompt_loader.search_prompts("TEST_PROMPT")

        assert len(results) == 1
        assert results[0].metadata.name == "TEST_PROMPT"

    def test_search_prompts_by_content(self, prompt_loader):
        """Test searching prompts by content"""
        results = prompt_loader.search_prompts("placeholder")

        assert len(results) == 1
        assert results[0].metadata.name == "TEST_PROMPT"

    def test_search_prompts_in_category(self, prompt_loader):
        """Test searching prompts within specific category"""
        results = prompt_loader.search_prompts("prompt", category="analysis")

        assert len(results) == 1
        assert results[0].metadata.category == "analysis"

    def test_caching_behavior(self, prompt_loader):
        """Test that prompts are cached globally after first load"""
        # Clear global cache first
        _load_prompt.cache_clear()

        # First call - cache miss
        prompt1 = prompt_loader.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 0

        # Second call - cache hit (even from different instance)
        prompt2 = prompt_loader.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.hits == 1
        assert prompt1 is prompt2  # Same object

        # Test that different instances share the cache
        another_loader = PromptLoader(prompt_loader.prompts_dir)
        prompt3 = another_loader.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.hits == 2  # Another cache hit
        assert prompt1 is prompt3  # Same object from global cache

    def test_reload_cache(self, prompt_loader):
        """Test cache clearing functionality"""
        # Load a prompt to populate global cache
        prompt_loader.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.currsize > 0

        # Clear cache using instance method
        prompt_loader.reload_cache()
        cache_info = _load_prompt.cache_info()
        assert cache_info.currsize == 0

    def test_global_cache_sharing(self, temp_prompts_dir):
        """Test that multiple PromptLoader instances share the global cache"""
        # Clear global cache first
        _load_prompt.cache_clear()

        # Create first loader and load a prompt
        loader1 = PromptLoader(temp_prompts_dir)
        prompt1 = loader1.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits == 0

        # Create second loader - should hit cache
        loader2 = PromptLoader(temp_prompts_dir)
        prompt2 = loader2.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.hits == 1
        assert prompt1 is prompt2  # Same object from global cache

        # Test with a third loader instance - should still hit cache
        loader3 = PromptLoader(temp_prompts_dir)
        prompt3 = loader3.get_prompt("coaching", "test-prompt")
        cache_info = _load_prompt.cache_info()
        assert cache_info.hits == 2
        assert prompt1 is prompt3  # Same object from global cache

    def test_variable_extraction(self, prompt_loader):
        """Test that variables are correctly extracted from prompt content"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")

        # Should extract 'variable' from prompt content
        assert "variable" in prompt.required_variables
        assert len(prompt.required_variables) == 1

    def test_variable_validation_missing(self, prompt_loader):
        """Test validation error when required variables are missing"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")

        with pytest.raises(ValueError, match="Missing required variables"):
            prompt.render()  # Missing 'variable'

        with pytest.raises(ValueError, match="variable"):
            prompt.render(wrong_var="value")

    def test_variable_validation_success(self, prompt_loader):
        """Test successful formatting with all required variables"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")
        formatted = prompt.render(variable="SUCCESS")

        assert "This is a test prompt with SUCCESS placeholder" in formatted
        assert "{variable}" not in formatted

    def test_variable_validation_extra_warning(self, prompt_loader, caplog):
        """Test warning for extra variables"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")

        # Should work but log warning
        formatted = prompt.render(variable="value", extra_var="extra")
        assert "test prompt with value" in formatted

        # Check warning was logged
        assert "Extra variables provided" in caplog.text
        assert "extra_var" in caplog.text

    def test_multiple_variables_extraction(self, prompt_loader):
        """Test extraction of multiple variables"""
        prompt = prompt_loader.get_prompt("analysis", "analysis-prompt")

        # Should extract both param1 and param2
        required_vars = prompt.required_variables
        assert "param1" in required_vars
        assert "param2" in required_vars
        assert len(required_vars) == 2

    def test_escaped_braces_ignored(self):
        """Test that escaped {{}} braces are not considered variables"""

        metadata = PromptMetadata(
            name="JSON_TEST", description="Test", category="test", source_file="test"
        )

        # Content with both regular {var} and escaped {{json}}
        content = """Process {user_input} and return JSON:
{{
    "result": "{processed_value}",
    "status": "{{fixed_status}}"
}}"""

        prompt = Prompt(metadata=metadata, _content=content)

        # Should only extract user_input and processed_value, not fixed_status
        required_vars = prompt.required_variables
        assert "user_input" in required_vars
        assert "processed_value" in required_vars
        assert "fixed_status" not in required_vars
        assert len(required_vars) == 2

    def test_no_variables_prompt(self, prompt_loader):
        """Test prompts with no variables"""
        prompt = prompt_loader.get_prompt("coaching", "another-prompt")

        # Should have no required variables
        assert len(prompt.required_variables) == 0

        # Should format successfully with no args
        formatted = prompt.render()
        assert "Simple prompt without variables" in formatted

    def test_required_variables_property_immutable(self, prompt_loader):
        """Test that required_variables property returns a copy"""
        prompt = prompt_loader.get_prompt("coaching", "test-prompt")

        vars1 = prompt.required_variables
        vars2 = prompt.required_variables

        # Should be separate objects (copies)
        assert vars1 is not vars2
        assert vars1 == vars2

        # Modifying one shouldn't affect the other
        vars1.add("new_var")
        assert "new_var" not in vars2
        assert "new_var" not in prompt.required_variables

    def test_parse_markdown_without_frontmatter(self, temp_prompts_dir):
        """Test parsing markdown file without frontmatter"""
        # Create a prompt without frontmatter
        simple_dir = temp_prompts_dir / "simple"
        simple_dir.mkdir()

        simple_prompt = simple_dir / "no-frontmatter.md"
        simple_prompt.write_text("Just plain content without metadata")

        loader = PromptLoader(prompts_dir=temp_prompts_dir)
        prompt = loader.get_prompt("simple", "no-frontmatter")

        assert prompt.metadata.name == "NO_FRONTMATTER"
        assert prompt.metadata.category == "simple"
        assert prompt.render() == "Just plain content without metadata"


class TestPromptLoaderWithRealPrompts:
    """Test with actual prompt files from the system"""

    def test_stage_transition_prompt_formatting(self):
        """Test that the actual STAGE_TRANSITION_SYSTEM_MESSAGE works correctly"""
        # Use the real prompts directory
        loader = PromptLoader()

        try:
            # Load the actual stage transition prompt
            prompt = loader.get_prompt("analysis", "stage-transition-system-message")

            # Format with test data
            formatted = prompt.render(
                current_stage="exploration",
                all_stages="exploration, action, completion",
                session_history="User discussed goals",
                stage_history="Stage specific history",
                missing_criteria="Some criteria missing",
                analysis_context="Analyze for transition",
            )

            # Verify the formatting worked
            assert "exploration" in formatted
            assert "Analyze for transition" in formatted

            # Verify JSON structure is preserved with single braces
            assert '"current_stage": string' in formatted
            assert '"transition_required": boolean' in formatted
            assert '"criteria_missing": [' in formatted

            # Ensure no double braces remain
            assert "{{" not in formatted
            assert "}}" not in formatted

        except FileNotFoundError:
            # Skip test if running in environment without prompt files
            pytest.skip("Prompt files not found - skipping real prompt test")


class TestPromptLoaderGlobalFunctions:
    """Test global convenience functions"""

    def test_get_prompt_loader_singleton(self):
        """Test that get_prompt_loader returns singleton"""
        with patch("app.services.prompt_loader._default_loader", None):
            loader1 = get_prompt_loader()
            loader2 = get_prompt_loader()
            assert loader1 is loader2

    @patch("app.services.prompt_loader.get_prompt_loader")
    def test_get_prompt_function(self, mock_get_loader):
        """Test global get_prompt convenience function"""
        mock_loader = Mock()
        mock_get_loader.return_value = mock_loader

        get_prompt("coaching", "test")

        mock_loader.get_prompt.assert_called_once_with("coaching", "test")

    @patch("app.services.prompt_loader.get_prompt_loader")
    def test_render_prompt_function(self, mock_get_loader):
        """Test global render_prompt convenience function"""
        mock_prompt = Mock()
        mock_prompt.render.return_value = "Formatted result"

        mock_loader = Mock()
        mock_loader.get_prompt.return_value = mock_prompt
        mock_get_loader.return_value = mock_loader

        result = render_prompt("coaching", "test", var1="value1")

        assert result == "Formatted result"
        mock_prompt.render.assert_called_once_with(var1="value1")


class TestPromptMetadata:
    """Test PromptMetadata dataclass"""

    def test_prompt_metadata_creation(self):
        """Test creating PromptMetadata"""
        metadata = PromptMetadata(
            name="TEST",
            description="Test description",
            category="testing",
            source_file="test_file",
        )

        assert metadata.name == "TEST"
        assert metadata.description == "Test description"
        assert metadata.category == "testing"
        assert metadata.source_file == "test_file"


class TestPrompt:
    """Test Prompt dataclass"""

    def test_prompt_creation(self):
        """Test creating Prompt with metadata"""
        metadata = PromptMetadata(
            name="TEST", description="Test", category="test", source_file="test"
        )

        prompt = Prompt(metadata=metadata, _content="Test content with {placeholder}")

        assert prompt.metadata == metadata
        assert prompt.render(placeholder="value") == "Test content with value"

    def test_prompt_format_method(self):
        """Test Prompt format method"""
        metadata = PromptMetadata(
            name="TEST", description="Test", category="test", source_file="test"
        )

        prompt = Prompt(
            metadata=metadata, _content="Hello {name}, you are {age} years old"
        )

        formatted = prompt.render(name="Alice", age=30)
        assert formatted == "Hello Alice, you are 30 years old"

    def test_json_template_with_double_braces(self):
        """Test that JSON templates with escaped braces work correctly"""
        metadata = PromptMetadata(
            name="JSON_PROMPT",
            description="JSON template test",
            category="test",
            source_file="test",
        )

        # This mimics the STAGE_TRANSITION_SYSTEM_MESSAGE format
        prompt = Prompt(
            metadata=metadata,
            _content="""Analyze the conversation for {stage_name}.

IMPORTANT: Your response must conform to the following JSON structure:
{{
    "current_stage": string,
    "next_stage": string,
    "transition_required": boolean,
    "criteria_missing": [
        {{
            "text": string,
            "priority": "critical" | "non_critical",
            "action": "blocked" | "considered"
        }}
    ],
    "return_indicators": {{
        "failed_attempts": integer,
        "confusion_detected": boolean
    }},
    "confidence": float
}}

Additional context: {additional_info}""",
        )

        # Format with variables
        formatted = prompt.render(
            stage_name="exploration", additional_info="This is extra context"
        )

        # Check that the variables are replaced
        assert "exploration" in formatted
        assert "This is extra context" in formatted
        assert "{stage_name}" not in formatted
        assert "{additional_info}" not in formatted

        # Check that the JSON structure braces are preserved as single braces
        assert '"current_stage": string' in formatted
        assert '"next_stage": string' in formatted
        assert '"transition_required": boolean' in formatted

        # Verify the JSON structure is preserved with single braces
        assert '{\n    "current_stage"' in formatted
        assert "}\n" in formatted
        assert '"criteria_missing": [' in formatted
        assert '        {\n            "text"' in formatted

        # Make sure we don't have double braces in the output
        assert "{{" not in formatted
        assert "}}" not in formatted

    def test_render_method_no_variables(self):
        """Test render() method with no variables"""
        metadata = PromptMetadata(
            name="TEST", description="Test", category="test", source_file="test"
        )
        prompt = Prompt(metadata=metadata, _content="Simple content")

        result = prompt.render()
        assert result == "Simple content"

    def test_render_method_with_variables(self):
        """Test render() method with variables"""
        metadata = PromptMetadata(
            name="TEST", description="Test", category="test", source_file="test"
        )
        prompt = Prompt(metadata=metadata, _content="Content with {var}")

        result = prompt.render(var="value")
        assert result == "Content with value"
