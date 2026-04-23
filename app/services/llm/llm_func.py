import asyncio
from typing import Any

import backoff
from openai import AsyncAzureOpenAI, RateLimitError

from app.util.constants import AZURE_CONFIG
from app.util.helpers import handle_exceptions

_knowledge_semaphore = asyncio.Semaphore(2)


@handle_exceptions
@backoff.on_exception(
    backoff.expo,
    (TimeoutError, RateLimitError, Exception),
    max_tries=3,
    base=2,
    jitter=backoff.full_jitter,
)
async def knowledge_llm_func(
    prompt: str,
    history_messages: list[dict] = [],  # noqa
    keyword_extraction: bool = False,
    **kwargs,  # noqa
) -> str | Any:
    """
    Custom LLM function that uses OpenAI to generate structured responses

    Args:
        prompt: User query or input text
        system_prompt: Optional system instructions
        history_messages: Previous conversation messages
        keyword_extraction: Whether this is for keyword extraction
        response_model: Optional Pydantic model for structured output
        **kwargs: Additional parameters for the model

    Returns:
        Either a string response or a structured response (if response_model
        is provided)

    """
    if keyword_extraction:
        async with _knowledge_semaphore:
            openai_client = AsyncAzureOpenAI(**AZURE_CONFIG)
            response = await openai_client.responses.create(
                input=prompt, model="gpt-4.1", store=True
            )
            return response.output_text

    return None
