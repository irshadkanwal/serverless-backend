from fastapi import APIRouter, Depends, HTTPException

from app.agents.summary.session_summary_agent import SessionSummaryAgent
from app.agents.summary.stage_summary_agent import StageSummaryAgent
from app.dependencies import get_stage_summary_agent, get_summary_agent
from app.models.summary_models import SessionSummaryContent, StageSummaryContent

router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("", response_model=str)
async def generate_summary(
    summary: SessionSummaryContent,
    summary_service: SessionSummaryAgent = Depends(get_summary_agent),
):
    try:
        return summary_service.process(summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {e!s}"
        )


stage_router = APIRouter(prefix="/stage/summary", tags=["stage-summary"])


@stage_router.post("", response_model=str)
async def generate_stage_summary(
    summary: StageSummaryContent,
    stage_summary_service: StageSummaryAgent = Depends(get_stage_summary_agent),
):
    try:
        return stage_summary_service.process(summary)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate stage summary: {e!s}"
        )
