"""
PromptLoader - Convenient loading system for markdown-based prompts.

This module provides a clean interface for loading prompts from markdown files
organized in categories. It supports global caching and template interpolation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

try:
    from app.util.helpers import get_logger

    logger = get_logger(__name__)
except ImportError:
    # Fallback logger for testing
    import logging

    logger = logging.getLogger(__name__)


# Global cache for parsed prompts - shared across all PromptLoader instances
@lru_cache(maxsize=256)
def _parse_markdown_file(file_path: Path) -> Prompt:
    """
    Parse a markdown file with frontmatter.

    This function is cached globally so all PromptLoader instances
    share the same cache, making it efficient for repeated use.
    """
    try:
        with file_path.open(encoding="utf-8") as f:
            content = f.read()

        # Split frontmatter and content
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter_str = parts[1]
                prompt_content = parts[2].strip()

                # Parse frontmatter
                frontmatter = yaml.safe_load(frontmatter_str)

                metadata = PromptMetadata(
                    name=frontmatter.get("name", file_path.stem),
                    description=frontmatter.get("description", ""),
                    category=frontmatter.get("category", "general"),
                    source_file=frontmatter.get("source_file", ""),
                )

                return Prompt(metadata=metadata, _content=prompt_content)

        # Fallback: treat entire file as content
        metadata = PromptMetadata(
            name=file_path.stem.replace("-", "_").upper(),
            description=f"Prompt from {file_path.name}",
            category=file_path.parent.name,
            source_file=file_path.stem,
        )

        return Prompt(metadata=metadata, _content=content.strip())

    except Exception as e:
        logger.error(f"Error parsing {file_path}: {e}")
        raise


# Global cache for prompt loading - keyed by (prompts_dir, category, prompt_name)
@lru_cache(maxsize=256)
def _load_prompt(prompts_dir: Path, category: str, prompt_name: str) -> Prompt:
    """
    Load a specific prompt by category and name.

    This function is cached globally so all PromptLoader instances
    share the same cache.
    """
    prompt_file = prompts_dir / category / f"{prompt_name}.md"

    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_file}")

    return _parse_markdown_file(prompt_file)


@dataclass
class PromptMetadata:
    """Metadata for a prompt."""

    name: str
    description: str
    category: str
    source_file: str


@dataclass
class Prompt:
    """A loaded prompt with metadata and content."""

    metadata: PromptMetadata
    _content: str
    _required_vars: set[str] = field(init=False)

    def __post_init__(self):
        """Extract required variables from the prompt content."""
        # Extract {variable} patterns while excluding escaped {{}} braces
        # This regex looks for {word} but not {{word}} or {word}}
        pattern = r"(?<!\{)\{([^{}]+)\}(?!\})"
        self._required_vars = set(re.findall(pattern, self._content))

    def render(self, **kwargs) -> str:
        """
        Render the prompt with optional variables.

        For prompts with no variables, simply returns the content.
        For prompts with variables, validates and substitutes them.

        Args:
            **kwargs: Variables to substitute in the prompt

        Returns:
            Rendered prompt content

        Raises:
            ValueError: If required variables are missing
        """
        # Validate required variables
        missing = self._required_vars - kwargs.keys()
        if missing:
            raise ValueError(
                f"Missing required variables for prompt '{self.metadata.name}': "
                f"{sorted(missing)}"
            )

        # Warn about extra variables (helps catch typos)
        extra = kwargs.keys() - self._required_vars
        if extra:
            logger.warning(
                f"Extra variables provided for prompt '{self.metadata.name}': "
                f"{sorted(extra)}"
            )

        return self._content.format(**kwargs)

    @property
    def required_variables(self) -> set[str]:
        """Get the set of required variables for this prompt."""
        return self._required_vars.copy()


class PromptLoader:
    """
    Loads and manages markdown-based prompts.

    Features:
    - Category-based organization (coaching, analysis, etc.)
    - Caching for performance
    - Template variable interpolation
    - Lazy loading

    Usage:
        # Load a specific prompt
        loader = PromptLoader()
        prompt = loader.get_prompt('coaching', 'coaching-response-instructions')

        # Render with variables
        rendered = prompt.render(reasoning_context="...", missing_criteria="...")

        # Category access
        coaching_prompts = loader.get_category('coaching')
    """

    def __init__(self, prompts_dir: Path | None = None):
        """
        Initialize the prompt loader.

        Args:
            prompts_dir: Directory containing markdown prompts.
                        Defaults to app/prompts_md/
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts_md"

        self.prompts_dir = Path(prompts_dir)

        if not self.prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompts_dir}")

    def get_prompt(self, category: str, prompt_name: str) -> Prompt:
        """
        Get a specific prompt by category and name.

        Args:
            category: Category name (e.g., 'coaching', 'analysis')
            prompt_name: Prompt filename without .md extension

        Returns:
            Prompt object with metadata and content
        """
        return _load_prompt(self.prompts_dir, category, prompt_name)

    def get_category(self, category: str) -> dict[str, Prompt]:
        """
        Load all prompts from a category.

        Args:
            category: Category name

        Returns:
            Dictionary mapping prompt names to Prompt objects
        """
        category_dir = self.prompts_dir / category

        if not category_dir.exists():
            logger.warning(f"Category directory not found: {category_dir}")
            return {}

        prompts = {}

        for md_file in category_dir.glob("*.md"):
            if md_file.name == "README.md":
                continue

            prompt_name = md_file.stem
            try:
                prompts[prompt_name] = self.get_prompt(category, prompt_name)
            except Exception as e:
                logger.error(f"Error loading {md_file}: {e}")

        return prompts

    def list_categories(self) -> list[str]:
        """List all available categories."""
        if not self.prompts_dir.exists():
            return []

        return [
            d.name
            for d in self.prompts_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def list_prompts(self, category: str) -> list[str]:
        """List all prompts in a category."""
        category_dir = self.prompts_dir / category

        if not category_dir.exists():
            return []

        return [f.stem for f in category_dir.glob("*.md") if f.name != "README.md"]

    def search_prompts(self, query: str, category: str | None = None) -> list[Prompt]:
        """
        Search for prompts by name or content.

        Args:
            query: Search term
            category: Optional category to limit search

        Returns:
            List of matching prompts
        """
        results = []
        query_lower = query.lower()

        categories = [category] if category else self.list_categories()

        for cat in categories:
            for prompt_name in self.list_prompts(cat):
                try:
                    prompt = self.get_prompt(cat, prompt_name)

                    # Search in name, description, and content
                    if (
                        query_lower in prompt.metadata.name.lower()
                        or query_lower in prompt.metadata.description.lower()
                        or query_lower in prompt._content.lower()
                    ):
                        results.append(prompt)

                except Exception as e:
                    logger.error(f"Error searching prompt {cat}/{prompt_name}: {e}")

        return results

    def reload_cache(self):
        """Clear the global cache to reload prompts from disk."""
        _load_prompt.cache_clear()
        _parse_markdown_file.cache_clear()


# Global instance
_default_loader = None


def get_prompt_loader() -> PromptLoader:
    """Get the default prompt loader instance."""
    global _default_loader
    if _default_loader is None:
        _default_loader = PromptLoader()
    return _default_loader


# Convenience functions
def get_prompt(category: str, prompt_name: str) -> Prompt:
    """Get a prompt using the default loader."""
    return get_prompt_loader().get_prompt(category, prompt_name)


def render_prompt(category: str, prompt_name: str, **kwargs) -> str:
    """Get and render a prompt in one call."""
    prompt = get_prompt(category, prompt_name)
    return prompt.render(**kwargs)


def clear_cache():
    """Clear the global prompt cache."""
    _load_prompt.cache_clear()
    _parse_markdown_file.cache_clear()
