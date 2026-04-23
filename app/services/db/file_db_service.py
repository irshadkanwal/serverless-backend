import traceback
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import TypeVar

import asyncpg

from app.models.knowledge_model import DocumentData
from app.util.constants import DB_PARAMS
from app.util.errors import DatabaseError
from app.util.helpers import async_lru_cache, get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class FileDatabaseService:
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
            conn = await asyncpg.connect(**DB_PARAMS)
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

    async def create_file_data(self, document: DocumentData) -> bool:
        """
        Create document pages in the PostgreSQL database without creating a File entry.

        Args:
            document: The document data to insert
        Returns:
            bool: True if successful, False otherwise

        """
        doc_id = document.id
        workspace = document.workspace
        doc_pages = document.pages_content

        if not doc_id or not workspace:
            logger.error("Document ID and workspace are required.")
            return False

        if not doc_pages or len(doc_pages) == 0:
            logger.warning(f"No page content provided for document {doc_id}")
            return True

        async def transaction_callback(conn):
            page_values = []
            for page_num, page_content in enumerate(doc_pages):
                page_id = f"{doc_id}_p{page_num}"
                page_number = page_num + 1
                page_values.append(
                    (page_id, workspace, page_content, doc_id, page_number)
                )

            if page_values:
                await conn.executemany(
                    (
                        'INSERT INTO knowledge."Page" (id, workspace, content, '
                        "file_id, number) VALUES ($1, $2, $3, $4, $5)"
                    ),
                    page_values,
                )
            return True

        result = await self.execute_transaction(
            transaction_callback, f"Error storing pages for document {doc_id}"
        )
        return result if result is not None else False

    async def fetch_page_content(
        self, workspace: str, file_id: str, page_spec: str
    ) -> str | None:
        """
        Fetch specific page content.

        Args:
            file_id: The file identifier
            page_spec: Optional page range in format 'start-end' (e.g., '1-3')
                    If None, returns full file content

        Returns:
            str: The requested content or None if not found/error

        """
        try:
            if "-" not in page_spec:
                try:
                    page_num = int(page_spec)
                    if page_num < 1:
                        logger.error(f"Invalid page number: {page_num}")
                        return None

                    async def fetch_single_page_callback(conn):
                        row = await conn.fetchrow(
                            (
                                'SELECT content FROM knowledge."Page" WHERE '
                                "workspace = $1 AND file_id = $2 AND number = $3"
                            ),
                            workspace,
                            file_id,
                            page_num,
                        )
                        return row["content"] if row else None

                    return await self.execute_transaction(
                        fetch_single_page_callback,
                        f"Error fetching page {page_num} for file {file_id}",
                    )

                except ValueError:
                    logger.error(f"Invalid page specification: {page_spec}")
                    return None
            else:
                try:
                    start, end = map(int, page_spec.split("-"))
                    if start < 1 or end < start:
                        logger.error(f"Invalid page range: {page_spec}")
                        return None
                except ValueError:
                    logger.error(
                        f"Invalid page range format: {page_spec}. "
                        f"Expected format: 'start-end'"
                    )
                    return None

                async def fetch_pages_callback(conn):
                    rows = await conn.fetch(
                        (
                            'SELECT content FROM knowledge."Page" WHERE workspace = $1 '
                            "AND file_id = $2 AND number BETWEEN $3 AND $4 "
                            "ORDER BY number"
                        ),
                        workspace,
                        file_id,
                        start,
                        end,
                    )

                    if not rows:
                        return None

                    contents = [row["content"] for row in rows]
                    return "\n".join(contents)

                return await self.execute_transaction(
                    fetch_pages_callback,
                    f"Error fetching page range {page_spec} for file {file_id}",
                )

        except Exception as e:
            logger.error(f"Error fetching file content: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            return None

    async def fetch_full_file_content(self, workspace: str, file_id: str) -> str | None:
        """
        Fetch full file content.

        Args:
            workspace: The workspace identifier
            file_id: The file identifier
        Returns:
            str: The full file content or None if not found/error

        """
        try:

            async def fetch_full_callback(conn):
                rows = await conn.fetch(
                    (
                        'SELECT content FROM knowledge."Page" WHERE workspace = $1 '
                        "AND file_id = $2 ORDER BY number"
                    ),
                    workspace,
                    file_id,
                )

                if not rows:
                    return None

                contents = [row["content"] for row in rows]
                return "\n".join(contents)

            return await self.execute_transaction(
                fetch_full_callback, f"Error fetching full content for file {file_id}"
            )

        except Exception as e:
            logger.error(f"Error fetching full file content: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            return None

    @async_lru_cache(maxsize=128)
    async def get_file_id_by_name(self, workspace: str, file_name: str) -> str | None:
        """
        Cached lookup for file IDs by name.

        Args:
            workspace: The workspace identifier
            file_name: The name of the file to look up

        Returns:
            str: The file ID if found, None otherwise

        """

        async def fetch_id_callback(conn):
            row = await conn.fetchrow(
                (
                    'SELECT id FROM public."KnowledgeFile" WHERE '
                    "user_id = $1 AND name = $2"
                ),
                workspace,
                file_name,
            )
            return row["id"] if row else file_name

        return await self.execute_transaction(
            fetch_id_callback, f"Error looking up file ID for {file_name}"
        )

    async def delete_file_data(self, workspace: str, file_id: str) -> bool:
        """
        Delete all data related to a file from the PostgreSQL database.

        Args:
            workspace: The workspace identifier
            file_id: The file identifier

        Returns:
            bool: True if successful, False otherwise

        """
        try:

            async def transaction_callback(conn):
                await conn.execute(
                    (
                        'DELETE FROM knowledge."Page" WHERE '
                        "workspace = $1 AND file_id = $2"
                    ),
                    workspace,
                    file_id,
                )

            await self.execute_transaction(
                transaction_callback, f"Error deleting file data for {file_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting file data: {e!s}")
            logger.error(f"[TRACEBACK] {traceback.format_exc()}")
            return False
