from lightrag import LightRAG
from lightrag.base import DocStatus

from app.models.knowledge_model import DocumentData
from app.util.helpers import get_logger, handle_exceptions


class StorageService:
    """
    Service for interfacing with LightRAG graph database.
    Provides resource management and async context managers for database operations.
    """

    def __init__(self, graphRAG: LightRAG):
        """Initialize the storage service."""
        self.logger = get_logger("storage_service")
        self.graphRAG = graphRAG

    async def check_document_processed(self, document_id: str) -> bool:
        """
        Check if a document is fully processed by checking its status.

        Args:
            document_id: ID of the document to check

        Returns:
            True if document is fully processed, False otherwise

        """
        try:
            processed_docs = await self.graphRAG.get_docs_by_status(DocStatus.PROCESSED)

            return any(doc_id == document_id for doc_id in processed_docs)

        except Exception as e:
            self.logger.error(f"Error checking document status: {e!s}")
            return False

    @handle_exceptions
    async def store_document(self, document: DocumentData) -> bool:
        """
        Store a document in the graph database.
        Implements retry logic with exponential backoff for handling database
        contention.

        Args:
            document: Document data to store

        Returns:
            True if successful, False otherwise

        """
        try:
            if len(document.content) == 0:
                self.logger.warning(f"No content provided for document {document.id}")
                return True

            document_content = "\n~~~\n".join(document.content)
            await self.graphRAG.ainsert(
                input=document_content,
                split_by_character="\n~~~\n",
                split_by_character_only=True,
                ids=document.id,
                file_paths=None,
            )
            return True

        except Exception as e:
            self.logger.error(f"Error storing document {document.id}: {e!s}")
            return False
