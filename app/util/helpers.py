import logging
import re
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar, cast

from .constants import DISPLAY_DATE_FORMAT
from .errors import AppError

T = TypeVar("T")


def get_logger(name: str) -> logging.Logger:
    """Configure and return a logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger


def format_iso_date_for_display(iso_date_str: str | None) -> str | None:
    """
    Safely parses an ISO 8601 date string and formats it for display.
    Handles formats like 'yyyy-mm-ddThh:mm:ss.sssZ'.
    """
    if not iso_date_str:
        return None
    try:
        iso_date_str = iso_date_str.replace("Z", "+00:00")
        dt_object = datetime.fromisoformat(iso_date_str)
        return dt_object.strftime(DISPLAY_DATE_FORMAT)
    except (ValueError, IndexError):
        get_logger(__name__).warning(f"Could not parse date string: {iso_date_str}")
        return None


def handle_exceptions[T](func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for consistent exception handling."""
    logger = get_logger(func.__module__)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except AppError as e:
            logger.error(f"Application error in {func.__name__}: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            logger.error(f"Occured at: {datetime.now()}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            logger.error(f"Occured at: {datetime.now()}")
            raise AppError(f"An unexpected error occurred: {e!s}")

    return cast("Callable[..., T]", wrapper)


def async_lru_cache(maxsize=128):
    """LRU Cache decorator for async functions."""

    def decorator(async_func):
        cache = {}

        @wraps(async_func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))

            if key in cache:
                return cache[key]

            result = await async_func(*args, **kwargs)

            if len(cache) >= maxsize:
                cache.pop(next(iter(cache)))

            cache[key] = result
            return result

        return wrapper

    return decorator


def parse_structured_response[T](
    text_content: str,
    response_model: type[T],
    allow_fallback: bool = False,
    logger: logging.Logger | None = None,
) -> T:
    """
    Parses a JSON string into a Pydantic model, with optional fallback for resilience.
    Extracts only the first JSON object if multiple are present.
    """
    if logger is None:
        logger = get_logger(__name__)
    text_content = text_content.strip()

    json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text_content)
    if json_match:
        first_json = json_match.group()

        remaining_text = text_content[json_match.end() :].strip()
        if remaining_text and remaining_text.startswith("{"):
            logger.warning("Multiple JSON objects detected. Using only the first one.")
        text_content = first_json

    try:
        return response_model.model_validate_json(text_content)
    except Exception as e:
        if not allow_fallback:
            logger.error(
                f"Failed to parse required JSON for {response_model.__name__}: {e}"
            )
            logger.error(f"Raw response: {text_content[:500]}")
            raise ValueError(
                f"LLM returned invalid JSON when a specific structure was required: {e}"
            )

        from app.models.coaching_model import AssistantResponse

        if response_model is AssistantResponse:
            if (
                "cannot assist" in text_content.lower()
                or "sorry" in text_content.lower()
            ):
                logger.info("Content moderated - returning refusal message")
            else:
                logger.warning(
                    "Failed to parse coaching response as JSON. Treating as plain text."
                    f" Error: {e}"
                )
                logger.warning(f"Raw LLM response: {text_content}")
            return cast("T", AssistantResponse(main_response=text_content))
        logger.error(
            f"Fallback is not supported for {response_model.__name__}. "
            "Strict parsing failed."
        )
        raise ValueError(
            f"LLM returned invalid JSON for a model that does not support fallback: {e}"
        )
