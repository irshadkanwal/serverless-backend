import logging

from mem0 import AsyncMemory
from pydantic import ValidationError

from app.models.models import UserInput

from .config import MemoryConfig
from .formatter import MemoryFormatter
from .generator import MemoryGenerator
from .models import (
    AllMemoriesRequest,
    DeleteRequest,
    MemoryAddRequest,
    MemoryResponse,
    MemorySearchRequest,
)


class MemoryService:
    def __init__(
        self,
        config: MemoryConfig | None = None,
        formatter: MemoryFormatter | None = None,
        generator: MemoryGenerator | None = None,
    ):
        self.config = config or MemoryConfig()
        self.formatter = formatter or MemoryFormatter()
        self.generator = generator or MemoryGenerator()
        self.mem0 = None

    async def _ensure_mem0_initialized(self):
        if self.mem0 is None:
            try:
                self.mem0 = await AsyncMemory.from_config(self.config.config)
            except Exception as e:
                logging.exception(f"Failed to initialize AsyncMemory: {e}")
                raise

    @property
    def memory_search_tools(self):
        return self.config.memory_search_tools

    def generate_memory_items(
        self, user_input: UserInput, coach_response: str
    ) -> list[dict[str, str]]:
        return self.generator.generate_memory_items(user_input, coach_response)

    async def add_memory(self, req: MemoryAddRequest) -> bool:
        try:
            await self._ensure_mem0_initialized()
            sanitized_text = self.formatter.sanitize_memory_text(req.text)
            await self.mem0.add(
                sanitized_text, user_id=req.user_id, metadata={"category": req.category}
            )
            return True
        except Exception as e:
            error_msg = str(e)
            if "payload" in error_msg:
                logging.exception(
                    f"mem0 payload error - likely invalid request parameters: {e}"
                )
                logging.exception(
                    f"Request details - user_id: {req.user_id}, "
                    f"text_length: {len(req.text) if req.text else 0}, "
                    f"category: {req.category}"
                )
            elif "SyntaxError" in error_msg and "-" in error_msg:
                logging.exception(
                    "Neo4j Syntax Error - likely invalid relationship name "
                    f"with hyphens: {e}"
                )
                logging.exception(f"Memory text that caused error: {req.text[:200]}...")
            else:
                logging.exception(f"Error adding memory: {e}")
            return False

    async def search_memory(self, req: MemorySearchRequest) -> MemoryResponse:
        try:
            await self._ensure_mem0_initialized()
            results = await self.mem0.search(req.query, user_id=req.user_id, limit=5)
            memories = self.formatter.format_memories(results["results"])
            relations = self.formatter.format_relations(results["relations"])
            return MemoryResponse(results=memories, relations=relations)
        except Exception as e:
            logging.exception(f"Error searching memory: {e}\n")
            return MemoryResponse(results=[], relations=[])

    async def check_if_already_asked(self, question: str, user_id: str) -> dict:
        result = await self.search_memory(
            MemorySearchRequest(query=question, user_id=user_id)
        )

        if not result.relations or (
            not result.results
            or (
                len(result.results) == 1
                and result.results[0].strip().lower() == "no memories found."
            )
        ):
            return {"already_asked": False, "results": ""}
        return {"already_asked": True, "results": result}

    async def all_memories(self, req: AllMemoriesRequest) -> MemoryResponse:
        try:
            await self._ensure_mem0_initialized()
            all_mems = await self.mem0.get_all(user_id=req.user_id)
            formatted = self.formatter.format_memories(all_mems)
            return MemoryResponse(results=formatted)
        except Exception as e:
            logging.exception(f"Error retrieving all memories: {e}")
            return MemoryResponse(results=[])

    async def delete_all_memories(self, req: DeleteRequest) -> bool:
        try:
            await self._ensure_mem0_initialized()
            await self.mem0.delete_all(user_id=req.user_id)
            return True
        except Exception as e:
            logging.exception(f"Error deleting memories: {e}")
            return False

    async def get_last_n_memories(self, user_id: str, n: int = 10) -> list[str]:
        await self._ensure_mem0_initialized()
        result = await self.mem0.get_all(user_id=user_id, limit=min(n * 3, 50))

        if isinstance(result, dict) and "results" in result:
            memories = result["results"]
        else:
            memories = result

        if memories and isinstance(memories[0], list):
            memories = [item for sublist in memories for item in sublist]

        sorted_memories = sorted(
            (m for m in memories if isinstance(m, dict)),
            key=lambda m: m.get("created_at", ""),
            reverse=True,
        )

        return self.formatter.format_memories(sorted_memories[:n])

    def process_memory_items(
        self, user_input: UserInput, memory_items: list[dict[str, str]]
    ) -> list[MemoryAddRequest]:
        processed_requests = []

        for mem in memory_items:
            try:
                text = mem.get("text")
                category = mem.get("category")

                memory_request = MemoryAddRequest(
                    text=text,
                    user_id=user_input.user_id,
                    category=category or "user_memory",
                )

                processed_requests.append(memory_request)

            except ValidationError as e:
                logging.warning(
                    f"Skipping memory item due to invalid data: {e}. Item: {mem}"
                )

        return processed_requests


# Singleton instance
mem0 = MemoryService()
