import traceback
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import TypeVar

import asyncpg

from app.models.knowledge_model import DocumentData
from app.util.constants import KNOWLEDGE_DB_PARAMS
from app.util.errors import DatabaseError
from app.util.helpers import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class KnowledgeDatabaseService:
    """Service class for database operations using asyncpg"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection using configuration parameters"""
        conn = None
        try:
            conn = await asyncpg.connect(**KNOWLEDGE_DB_PARAMS)
            yield conn
        except Exception as e:
            logger.error(f"Error connecting to database: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            raise DatabaseError(f"Failed to connect to database: {e!s}")
        finally:
            if conn:
                await conn.close()

    async def execute_transaction(
        self,
        callback: Callable[[asyncpg.Connection], T],
        error_msg: str = "Database operation failed",
    ) -> T | None:
        """
        Execute a callback function within a database transaction.

        Args:
            callback: Async function that takes a connection and returns a result
            error_msg: Custom error message for logging

        Returns:
            The result of the callback function or None if an error occurred

        """
        try:
            async with self.get_connection() as conn, conn.transaction():
                return await callback(conn)
        except Exception as e:
            logger.error(f"{error_msg}: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            return None

    async def fetch_file_content(self, file_id: str) -> str | None:
        """
        Fetch file content, either full content or specific page range.

        Args:
            file_id: The file identifier

        Returns:
            str: The requested content or None if not found/error

        """
        try:

            async def fetch_full_callback(conn):
                row = await conn.fetchrow(
                    "SELECT content FROM public.lightrag_doc_full WHERE id = $1",
                    file_id,
                )
                return row["content"] if row else None

            return await self.execute_transaction(
                fetch_full_callback, f"Error fetching full content for file {file_id}"
            )

        except Exception as e:
            logger.error(f"Error fetching file content: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            return None

    async def delete_document_data(self, document: DocumentData) -> bool:
        """
        Delete all data related to a document from the PostgreSQL database.

        Args:
            document: The document to delete

        Returns:
            bool: True if successful, False otherwise

        """
        doc_id = document.id
        workspace = document.workspace

        chunk_ids = await self._get_document_chunk_ids(workspace, doc_id)
        if not chunk_ids:
            logger.warning(
                f"No chunks found for document {doc_id} in workspace {workspace}"
            )

        async def transaction_callback(conn):
            await conn.execute(
                (
                    "DELETE FROM LIGHTRAG_DOC_CHUNKS WHERE workspace = $1 "
                    "AND full_doc_id = $2"
                ),
                workspace,
                doc_id,
            )

            await conn.execute(
                "DELETE FROM LIGHTRAG_DOC_FULL WHERE workspace = $1 AND id = $2",
                workspace,
                doc_id,
            )

            await conn.execute(
                "DELETE FROM LIGHTRAG_LLM_CACHE WHERE workspace = $1 AND id = $2",
                workspace,
                doc_id,
            )

            if chunk_ids:
                entity_query = """
                DELETE FROM LIGHTRAG_VDB_ENTITY
                WHERE workspace = $1 AND
                      chunk_ids && $2::VARCHAR(255)[]
                """
                await conn.execute(entity_query, workspace, chunk_ids)

                relation_query = """
                DELETE FROM LIGHTRAG_VDB_RELATION
                WHERE workspace = $1 AND
                      chunk_ids && $2::VARCHAR(255)[]
                """
                await conn.execute(relation_query, workspace, chunk_ids)

            await conn.execute(
                "DELETE FROM LIGHTRAG_DOC_STATUS WHERE workspace = $1 AND id = $2",
                workspace,
                doc_id,
            )
            return True

        result = await self.execute_transaction(
            transaction_callback, f"Error deleting document data for {doc_id}"
        )
        return result if result is not None else False

    async def _get_document_chunk_ids(self, workspace: str, doc_id: str) -> list[str]:
        """
        Get all chunk IDs associated with a document.

        Args:
            workspace: The workspace identifier
            doc_id: The document ID

        Returns:
            List[str]: List of chunk IDs associated with the document

        """

        async def query_callback(conn):
            rows = await conn.fetch(
                (
                    "SELECT id FROM LIGHTRAG_DOC_CHUNKS WHERE workspace = $1 "
                    "AND full_doc_id = $2"
                ),
                workspace,
                doc_id,
            )
            return [row["id"] for row in rows]

        result = await self.execute_transaction(
            query_callback, f"Error getting chunk IDs for document {doc_id}"
        )
        return result if result is not None else []
