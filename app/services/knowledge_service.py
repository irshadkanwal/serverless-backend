import asyncio
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path

from lightrag import LightRAG, QueryParam
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
from lightrag.prompt import PROMPTS
from lightrag.utils import TiktokenTokenizer, setup_logger

from app.models.knowledge_model import (
    DocumentData,
    KnowledgeResponse,
    KnowledgeSearchRequest,
)
from app.services.llm.llm_func import knowledge_llm_func
from app.services.notification_service import NotificationService
from app.services.prompt_loader import PromptLoader
from app.services.storage_service import StorageService
from app.util.constants import KNOWLEDGE_KEYWORDS, TONE_KEYWORDS
from app.util.errors import KnowledgeGraphError
from app.util.helpers import get_logger, handle_exceptions

setup_logger("storage_service", "DEBUG")


class KnowledgeService:
    """Service for managing knowledge base data."""

    def __init__(self):
        """Initialize the storage service."""
        self.prompts = PromptLoader()
        self.work_dir = "./graph_storage"
        Path(self.work_dir).mkdir(parents=True, exist_ok=True)

        self.logger = get_logger("storage_service")

        self.knowledge_search_tool = {
            "type": "function",
            "name": "searchKnowledge",
            "description": (
                "Search the coach's curated knowledge base containing professional "
                "coaching frameworks, methodologies, and practice materials. "
                "Use this ONLY when the user's question relates to coaching "
                "concepts, techniques, or situations that would benefit from "
                "the coach's structured knowledge resources. Do NOT use for "
                "general information or file searches - this is specifically "
                "for coaching-specific knowledge retrieval."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query to find relevant coaching knowledge, "
                            "methodologies, or practice information that could "
                            "help address the user's session message. Include key "
                            "coaching concepts, techniques, or topics mentioned "
                            "by the user."
                        ),
                    }
                },
                "required": ["query"],
            },
        }

    @asynccontextmanager
    async def initialize_rag(
        self,
        workspace: str,
        llm_model_func: Callable = gpt_4o_mini_complete,
        timeout: int = 10,
    ):
        """
        Get or create a LightRAG instance for the given workspace.
        Returns an async context manager for proper resource management.

        Args:
            workspace: Workspace name
            namespace: Namespace prefix

        Yields:
            Configured LightRAG instance

        """
        try:
            os.environ["POSTGRES_WORKSPACE"] = workspace
            os.environ["POSTGRES_DATABASE"] = os.getenv(
                "KNOWLEDGE_DATABASE", "postgres"
            )

            working_dir = f"{self.work_dir}/{workspace}"
            Path(working_dir).mkdir(parents=True, exist_ok=True)

            rag = LightRAG(
                working_dir=working_dir,
                embedding_func=openai_embed,
                llm_model_func=llm_model_func,
                auto_manage_storages_states=False,
                enable_llm_cache_for_entity_extract=True,
                kv_storage="PGKVStorage",
                doc_status_storage="PGDocStatusStorage",
                graph_storage="PGGraphStorage",
                vector_storage="PGVectorStorage",
                enable_llm_cache=True,
                tokenizer=TiktokenTokenizer(),
            )

            try:
                await asyncio.wait_for(rag.initialize_storages(), timeout=timeout)
                await asyncio.wait_for(initialize_pipeline_status(), timeout=timeout)

                rag.chunk_entity_relation_graph.embedding_func = rag.embedding_func

                yield rag
            except TimeoutError:
                self.logger.error("Timeout occurred while initializing RAG storages")
                raise KnowledgeGraphError("Connection to knowledge database timed out")

        except Exception as e:
            import traceback

            self.logger.error(f"Failed to initialize storages: {e}")
            self.logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            raise KnowledgeGraphError(
                f"Failed to initialize knowledge graph storages: {e!s}"
            )
        finally:
            try:
                await rag.finalize_storages()
            except (TimeoutError, Exception) as e:
                self.logger.warning(f"Error during storage finalization: {e!s}")

    async def process_document_in_background(
        self, document_data: DocumentData, notification_service: NotificationService
    ):
        """
        Background task to process and store document in the knowledge graph.
        """
        try:
            async with self.initialize_rag(document_data.workspace) as graph_rag:
                storage_service = StorageService(graph_rag)

                insert_success = await storage_service.store_document(document_data)

                status = "complete" if insert_success else "error"

                notification_result = (
                    await notification_service.notify_processing_complete(
                        document_data, status
                    )
                )
                if not notification_result:
                    self.logger.error(
                        f"Failed to send notification for document: {document_data.id}"
                    )

        except Exception as e:
            notification_result = await notification_service.notify_processing_complete(
                document_data, "error"
            )
            self.logger.error(f"Notification result: {notification_result}")
            self.logger.error(
                f"Error during background processing of document "
                f"{document_data.id}: {e!s}"
            )

    @handle_exceptions
    async def retrive_knowledge_context(
        self, rag: LightRAG, query: str, knowledge_ids: list = None, timeout: int = 10
    ) -> str | None:
        """
        Retrieve knowledge context based on keywords and query.

        Args:
            workspace: User's Workspace name
            query: User query or input text
            hl_keywords: High-level keywords
            ll_keywords: Low-level keywords
            knowledge_ids: List of knowledge file IDs to filter the query

        Returns:
            Retrieved context as a string

        """
        try:
            query_params = QueryParam(
                mode="hybrid",
                top_k=2,
                only_need_context=True,
                ids=knowledge_ids,
            )
            response = await asyncio.wait_for(
                rag.aquery(query, param=query_params), timeout=timeout
            )

            if response == PROMPTS["fail_response"]:
                return None

            return response

        except TimeoutError:
            self.logger.warning(
                f"Knowledge retrieval timed out after {timeout} seconds"
            )
            return None
        except Exception as e:
            self.logger.error(f"Error querying knowledge graph: {e!s}")
            raise KnowledgeGraphError(f"Failed to query knowledge graph: {e!s}")

    async def searchKnowledge(self, req: KnowledgeSearchRequest) -> KnowledgeResponse:
        """
        Search knowledge base using function tool pattern.

        Args:
            req: KnowledgeSearchRequest containing query, user_id, and
                optional knowledge_ids

        Returns:
            KnowledgeResponse with context

        """
        try:
            async with self.initialize_rag(
                req.workspace, knowledge_llm_func
            ) as rag_service:
                knowledge_context = await self.retrive_knowledge_context(
                    rag_service, req.query, req.knowledge_ids
                )

                return KnowledgeResponse(
                    context=knowledge_context,
                )

        except KnowledgeGraphError as e:
            self.logger.warning(f"Knowledge search error: {e}")
            return KnowledgeResponse(context=None)
        except Exception as e:
            self.logger.error(f"Unexpected error in knowledge search: {e}")
            return KnowledgeResponse(context=None)

    def is_knowledge_query(self, queries: list[str]) -> bool:
        """Determine if file search queries are knowledge-related vs tone-related"""
        all_queries = " ".join(queries).lower()

        knowledge_score = sum(
            1 for keyword in KNOWLEDGE_KEYWORDS if keyword in all_queries
        )
        tone_score = sum(1 for keyword in TONE_KEYWORDS if keyword in all_queries)

        # If clearly tone-related, don't request the knowledge search
        if tone_score > 0 and knowledge_score == 0:
            return False

        return knowledge_score > 0

    async def handle_knowledge_search_with_context(
        self,
        query: str,
        workspace: str,
        knowledge_ids: list[str],
        messages: list[dict[str, str]],
    ) -> None:
        """Handle knowledge search and add context to messages if found"""
        if not workspace:
            self.logger.warning("Knowledge search called but no assistant_id provided")
            return

        knowledge_data = {
            "query": query,
            "workspace": workspace,
            "knowledge_ids": knowledge_ids if knowledge_ids else [],
        }
        knowledge_context = await self.searchKnowledge(
            KnowledgeSearchRequest(**knowledge_data)
        )

        if knowledge_context.context:
            messages.append(
                {
                    "role": "system",
                    "content": self.prompts.get_prompt(
                        "coaching", "knowledge-instructions"
                    ).render(context_data=knowledge_context.context),
                }
            )
        else:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "A file search ALREADY PERFORMED, but no relevant "
                        "information was found for the query. STOP calling "
                        "the file search tool."
                    ),
                }
            )
