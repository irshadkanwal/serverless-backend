import asyncio
import json
from typing import Any, TypeVar

import backoff
from openai import AsyncAzureOpenAI, AsyncOpenAI, InternalServerError, RateLimitError
from openai.types import Moderation

from app.models.coaching_model import AssistantResponse
from app.models.coaching_request_model import CoachingRequest
from app.models.llm_config_model import LLMConfig
from app.services.knowledge_service import KnowledgeService
from app.services.memory.memory_service import MemorySearchRequest, mem0
from app.util.constants import AZURE_CONFIG
from app.util.errors import LLMError
from app.util.helpers import get_logger, handle_exceptions

T = TypeVar("T")


class LLMService:
    def __init__(self, config: LLMConfig | None = None):
        self.config = config if config is not None else self._default_config()
        self.azure_openai_client = AsyncAzureOpenAI(**AZURE_CONFIG)
        self.openai_client = AsyncOpenAI()
        self.logger = get_logger(__name__)
        self.knowledge_service = KnowledgeService()
        self.azure_semaphore = asyncio.Semaphore(12)
        self.openai_semaphore = asyncio.Semaphore(25)

    def _default_config(self) -> LLMConfig:
        """
        Provides the default configuration for the language model.

        Returns:
            LLMConfig: An instance of LLMConfig with default parameters set
                for the language model.

        """
        return LLMConfig(
            model="gpt-4.1",
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.2,
        )

    def _get_completion_params(
        self, response_format: dict | None = None
    ) -> dict[str, Any]:
        """Get all completion parameters from config"""
        params = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
        }
        if response_format:
            params["response_format"] = response_format
        return params

    @backoff.on_exception(
        backoff.expo,
        (TimeoutError, RateLimitError, InternalServerError),
        max_tries=3,
        base=2,
        jitter=backoff.full_jitter,
    )
    async def moderate_message(self, message: str) -> Moderation:
        """Moderate message with current configuration"""
        async with self.openai_semaphore:
            response = await self.openai_client.moderations.create(
                input=message, model="omni-moderation-latest"
            )
            return response.results[0]

    @backoff.on_exception(
        backoff.expo,
        (TimeoutError, RateLimitError, Exception),
        max_tries=3,
        base=2,
        jitter=backoff.full_jitter,
    )
    async def generate_response(self, messages: list[dict[str, str]]) -> str:
        """Generate text response with current configuration"""
        async with self.azure_semaphore:
            response = await self.azure_openai_client.responses.create(
                input=messages,
                model=self.config.model,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
            )

            return response.output_text

    @backoff.on_exception(
        backoff.expo,
        (TimeoutError, RateLimitError, Exception),
        max_tries=3,
        base=2,
        jitter=backoff.full_jitter,
    )
    async def generate_json_response(self, messages: list[dict[str, str]]) -> str:
        """Generate JSON response with current configuration"""
        async with self.azure_semaphore:
            response = await self.azure_openai_client.responses.create(
                input=messages,
                model=self.config.model,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                text={"format": {"type": "json_object"}},
            )

            return response.output_text

    @handle_exceptions
    @backoff.on_exception(
        backoff.expo,
        (TimeoutError, LLMError, RateLimitError, InternalServerError),
        max_tries=3,
        base=2,
        max_time=300,
        jitter=backoff.full_jitter,
    )
    async def generate_coaching_response(
        self, request: CoachingRequest
    ) -> AssistantResponse:
        """
        Generate structured response using the Responses API with current configuration.
        This function will loop to handle multiple function calls from the LLM.

        Args:
            request: CoachingRequest containing all parameters for response generation

        Returns:
            Instance of response_model containing the structured response

        Raises:
            Exception: If response generation or parsing fails

        """
        common_params = self._configure_tools_and_params(request)

        max_function_calls = 3
        called_functions = set()

        for i in range(max_function_calls):
            common_params["input"] = request.messages

            try:
                async with self.azure_semaphore:
                    response = await self.azure_openai_client.responses.create(
                        **common_params
                    )

            except Exception as e:
                self.logger.error(
                    f"Azure OpenAI API call failed on attempt "
                    f"{i + 1}/{max_function_calls}"
                )
                self.logger.error(f"Error type: {type(e).__name__}")
                self.logger.error(f"Error message: {e!s}")
                if hasattr(e, "response") and e.response:
                    self.logger.error(
                        f"HTTP status code: "
                        f"{getattr(e.response, 'status_code', 'unknown')}"
                    )
                    self.logger.error(
                        f"Response headers: {getattr(e.response, 'headers', 'unknown')}"
                    )
                self.logger.error(f"Request model: {common_params.get('model')}")
                self.logger.error(f"Request messages count: {len(request.messages)}")
                self.logger.error(
                    f"Azure semaphore value: {self.azure_semaphore._value}"
                )
                raise

            has_function_calls = False
            if response.output:
                has_function_calls = any(
                    o.type in ["function_call", "file_search_call"]
                    for o in response.output
                )

            if has_function_calls:
                current_function_calls = set()
                for o in response.output:
                    if o.type == "function_call":
                        current_function_calls.add(o.name)
                    elif o.type == "file_search_call":
                        current_function_calls.add("file_search")

                already_called = current_function_calls.intersection(called_functions)
                if already_called:
                    break

                called_functions.update(current_function_calls)
                await self._handle_function_calls(
                    response,
                    request.messages,
                    request.user_id,
                    request.workspace,
                    request.knowledge_ids,
                )

                function_names = ", ".join(current_function_calls)
                request.messages.append(
                    {
                        "role": "system",
                        "content": (
                            f"Context from {function_names} has been added above. "
                            f"Now generate your final JSON response using this "
                            f"context. Do not call any more functions."
                        ),
                    }
                )
                continue

            if response.output_text and response.output_text.strip():
                return self._parse_structured_response(
                    response.output_text, AssistantResponse, allow_fallback=True
                )

            break
        return None

    @handle_exceptions
    @backoff.on_exception(
        backoff.expo,
        (TimeoutError, LLMError, RateLimitError, InternalServerError),
        max_tries=3,
        base=2,
        max_time=300,
        jitter=backoff.full_jitter,
    )
    async def system_task_processing(
        self, messages: list[dict[str, str]], response_model: type[T]
    ) -> T:
        """
        Generate structured response using instructor with current configuration

        Args:
            messages: List of message dictionaries with role and content
            instructions: Instructions for the assistant

        Returns:
            Instance of response_model containing the structured response

        Raises:
            Exception: If response generation or parsing fails

        """
        async with self.azure_semaphore:
            response = await self.azure_openai_client.responses.create(
                input=messages,
                text={"format": {"type": "json_object"}},
                model="gpt-4.1-mini",
                store=False,
            )

        return self._parse_structured_response(
            response.output_text, response_model, allow_fallback=False
        )

    @property
    def current_config(self) -> dict[str, Any]:
        """Get current configuration as dictionary"""
        return self.config.model_dump()

    ### Private methods ###

    @handle_exceptions
    def _parse_structured_response(
        self, text_content: str, response_model: type[T], allow_fallback: bool
    ) -> T:
        """
        Parses a JSON string into a Pydantic model, with an optional
        fallback for resilience.
        """
        from app.util.helpers import parse_structured_response

        return parse_structured_response(
            text_content, response_model, allow_fallback, self.logger
        )

    @handle_exceptions
    def _configure_tools_and_params(self, request: CoachingRequest) -> dict[str, Any]:
        """Configure tools and common parameters for coaching response"""
        tools = mem0.memory_search_tools
        if request.knowledge_ids and len(request.knowledge_ids) > 0:
            tools.append(self.knowledge_service.knowledge_search_tool)

        common_params = {
            "model": self.config.model,
            "instructions": request.instructions,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "text": {"format": {"type": "json_object"}},
            "tools": [] if request.is_initial_message else tools,
            "tool_choice": "auto",
        }

        if request.tone_examples and request.tone_examples != "none":
            common_params["tools"].append(
                {
                    "type": "file_search",
                    "vector_store_ids": [request.tone_examples],
                    "max_num_results": 5,
                }
            )

        return common_params

    @handle_exceptions
    async def _handle_function_calls(
        self,
        response,
        messages: list[dict[str, str]],
        user_id: str,
        workspace: str | None,
        knowledge_ids: list[str] | None,
    ):
        """Handle function calls from the initial response"""
        for output in response.output:
            if output.type == "function_call":
                match output.name:
                    case "searchMemory":
                        args_dict = json.loads(output.arguments)
                        memory_query = args_dict.get("query", messages[-2]["content"])
                        memory_data = {
                            "query": memory_query,
                            "user_id": user_id,
                            "category": "user_memory",
                        }
                        memory_context = await mem0.search_memory(
                            MemorySearchRequest(**memory_data)
                        )

                        context_parts = []
                        if memory_context.results:
                            context_parts.append("\n".join(memory_context.results))

                        if memory_context.relations:
                            relations_str = ", ".join(
                                r.lower() for r in memory_context.relations
                            )
                            context_parts.append(f"I also recall that {relations_str}.")

                        if context_parts:
                            system_message = (
                                "Here is some relevant context from our previous"
                                f" conversations:\n{' '.join(context_parts).strip()}"
                            )
                            messages.append(
                                {"role": "system", "content": system_message}
                            )

                    case "searchKnowledge":
                        if isinstance(output.arguments, dict):
                            knowledge_query = output.arguments.get(
                                "query", messages[-1]["content"]
                            )
                        elif isinstance(output.arguments, str):
                            try:
                                args_dict = json.loads(output.arguments)
                                knowledge_query = args_dict.get(
                                    "query", messages[-1]["content"]
                                )
                            except (json.JSONDecodeError, AttributeError):
                                knowledge_query = messages[-1]["content"]
                        else:
                            knowledge_query = messages[-1]["content"]
                        await (
                            self.knowledge_service.handle_knowledge_search_with_context(
                                knowledge_query, workspace, knowledge_ids, messages
                            )
                        )
                    case _:
                        self.logger.warning(
                            f"Unknown function call {output.name} with arguments "
                            f"{output.arguments}. Ignoring."
                        )
                        continue

            if output.type == "file_search_call" and (
                knowledge_ids
                and len(knowledge_ids) > 0
                and workspace
                and self.knowledge_service.is_knowledge_query(output.queries)
            ):
                knowledge_query = (
                    " | ".join(output.queries)
                    if output.queries
                    else messages[-1]["content"]
                )
                await self.knowledge_service.handle_knowledge_search_with_context(
                    knowledge_query, workspace, knowledge_ids, messages
                )
