from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Security,
)

from app.agents.analyzer.stage_transition_analyzer import StageTransitionAnalyzer
from app.dependencies import (
    get_coaching_service,
    get_limiter,
    get_stage_transition_analyzer,
)
from app.middleware.security import get_api_key
from app.models.models import CoachingResponse, UserInput
from app.services.coaching_service import CoachingService
from app.services.memory.memory_service import mem0
from app.util.helpers import get_logger

logger = get_logger(__name__)
limiter = get_limiter()

router = APIRouter(prefix="/coaching", tags=["coaching"])


@router.post("", response_model=CoachingResponse)
@limiter.limit("500/minute")
async def handle_coaching_interaction(
    request: Request,  # noqa
    background_tasks: BackgroundTasks,
    user_input: UserInput,
    coaching_service: CoachingService = Depends(get_coaching_service),
    stage_transition_analyzer: StageTransitionAnalyzer = Depends(
        get_stage_transition_analyzer
    ),
    _: str = Security(get_api_key),
):
    """
    Handle a coaching interaction.

    This endpoint receives a user input, performs content moderation,
    processes the message through the coaching service, and enqueues
    a background task for stage transition analysis.

    Args:
        background_tasks (BackgroundTasks): FastAPI background tasks manager.
        user_input (UserInput): The incoming user input with chat and message details.
        coaching_service (CoachingService): Service to process and respond to
            coaching messages.
        stage_transition_analyzer (StageTransitionAnalyzer): Analyzer to evaluate
            and notify stage transitions.

    Returns:
        CoachingResponse: Contains the chat ID and the coaching service response.

    Raises:
        HTTPException: Propagates HTTP exceptions or wraps internal errors with a
            500 status.

    """
    try:
        chat_id = user_input.chat_id or "default_id"

        moderation_result = await coaching_service.input_moderation(
            user_input.assistant_id, user_input.newMessage.content
        )

        if moderation_result:
            return CoachingResponse(chat_id=chat_id, response=moderation_result)

        response, assistant_data = await coaching_service.handle_message(user_input)

        memory_items = mem0.generate_memory_items(user_input, response)
        _update_user_memory(background_tasks, user_input, memory_items)

        if assistant_data is not None:
            background_tasks.add_task(
                stage_transition_analyzer.analyze,
                user_input=user_input,
                assistant_response=response,
                assistant_data=assistant_data,
            )

        return CoachingResponse(chat_id=chat_id, response=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in handle_coaching_interaction: {e!s}")
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {e!s}")


def _update_user_memory(
    background_tasks: BackgroundTasks,
    user_input: UserInput,
    memory_items: list[dict[str, str]],
):
    memory_requests = mem0.process_memory_items(user_input, memory_items)
    for memory_request in memory_requests:
        background_tasks.add_task(mem0.add_memory, req=memory_request)
