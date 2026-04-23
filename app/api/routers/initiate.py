from fastapi import APIRouter, Depends, HTTPException, Request, Security

from app.dependencies import get_coaching_service, get_limiter
from app.middleware.security import get_api_key
from app.models.models import CoachingResponse, InitialMessageRequest
from app.services.coaching_service import CoachingService
from app.util.helpers import get_logger, handle_exceptions

logger = get_logger(__name__)
limiter = get_limiter()

router = APIRouter(prefix="/initiate-conversation", tags=["initiate"])


@handle_exceptions
@router.post("", response_model=CoachingResponse)
@limiter.limit("10/minute")
async def generate_initial_message(
    request: Request,  # noqa
    message_request: InitialMessageRequest,
    coaching_service: CoachingService = Depends(get_coaching_service),
    _: str = Security(get_api_key),
):
    """
    Generate an initial message for a conversation.

    This endpoint generates an initial message based on the assistant ID and
    user ID provided.
    It returns a CoachingResponse containing the chat ID and the generated message.

    Args:
        request (InitialMessageRequest): The request object containing assistant ID
            and user ID.
        coaching_service (CoachingService): Service to process and respond to
            coaching messages.

    Returns:
        CoachingResponse: Contains the chat ID and the generated initial message.

    Raises:
        HTTPException: Propagates HTTP exceptions or wraps internal errors with a
            500 status.

    """
    try:
        response = await coaching_service.generate_initial_message(message_request)

        return CoachingResponse(chat_id="", response=response)
    except Exception as e:
        import traceback

        logger.error(traceback.format_exc())
        logger.error(f"Error generating initial message: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
