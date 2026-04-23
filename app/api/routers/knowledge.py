from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Security,
)

from app.dependencies import (
    get_db_service,
    get_knowledge_db_service,
    get_knowledge_service,
    get_limiter,
    get_notification_service,
)
from app.middleware.security import get_api_key
from app.models.knowledge_model import BuildKnowledgeResponse, DocumentData
from app.services.db.file_db_service import FileDatabaseService
from app.services.db.knowledge_db_service import KnowledgeDatabaseService
from app.services.knowledge_service import KnowledgeService
from app.services.notification_service import NotificationService
from app.util.helpers import get_logger, handle_exceptions

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
limiter = get_limiter()

logger = get_logger("knowledge_router")


@handle_exceptions
@router.post("/build", response_model=BuildKnowledgeResponse)
@limiter.limit("100/hour")
async def build_knowledge_graph(
    request: Request,  # noqa
    document_data: DocumentData,
    background_tasks: BackgroundTasks,
    knowledge_service: KnowledgeService = Depends(get_knowledge_service),
    db_service: FileDatabaseService = Depends(get_db_service),
    notification_service: NotificationService = Depends(get_notification_service),
    _: str = Security(get_api_key),
):
    """
    Store a document in the knowledge graph.
    This endpoint returns immediately and processes the document in the background.
    """
    background_tasks.add_task(
        knowledge_service.process_document_in_background,
        document_data,
        notification_service,
    )

    background_tasks.add_task(db_service.create_file_data, document_data)

    return BuildKnowledgeResponse(
        status="processing", message="Document processing has been queued"
    )


@handle_exceptions
@router.delete("/delete")
@limiter.limit("100/hour")
async def delete_document(
    request: Request,  # noqa
    document_data: DocumentData,
    db_service: FileDatabaseService = Depends(get_db_service),
    knowledge_service: KnowledgeDatabaseService = Depends(get_knowledge_db_service),
    _: str = Security(get_api_key),
):
    """
    Delete a document from the knowledge graph.
    """
    try:
        delete_success = await db_service.delete_file_data(
            document_data.workspace, document_data.id
        )
        delete_success = await knowledge_service.delete_document_data(document_data)
        return {"success": delete_success}
    except Exception as e:
        import traceback

        logger.error(traceback.format_exc())
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")
