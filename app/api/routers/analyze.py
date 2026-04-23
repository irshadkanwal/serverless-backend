from fastapi import APIRouter, Depends

from app.agents.analyzer.content_analyzer import ContentAnalyzer
from app.agents.analyzer.context_analyzer import ContextNeedAnalyzer
from app.agents.analyzer.emotion_analyzer import EmotionalAnalyzer
from app.agents.analyzer.stage_transition_analyzer import StageTransitionAnalyzer
from app.dependencies import get_context_manager, get_llm_service, get_prompt_manager
from app.models.analyzer_model import (
    AnalysisRequest,
    ContentAnalysisResult,
    ContextNeedResult,
    EmotionalAnalysisResult,
    StageTransitionResult,
)

router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/stage", response_model=StageTransitionResult)
async def analyze_stage_transition(
    request: AnalysisRequest,
    llm_service=Depends(get_llm_service),
    prompt_manager=Depends(get_prompt_manager),
):
    analyzer = StageTransitionAnalyzer(llm_service, prompt_manager)
    return await analyzer.analyze(request)


@router.post("/content", response_model=ContentAnalysisResult)
async def analyze_content(
    request: AnalysisRequest,
    llm_service=Depends(get_llm_service),
    prompt_manager=Depends(get_prompt_manager),
):
    analyzer = ContentAnalyzer(llm_service, prompt_manager)
    return await analyzer.analyze(request)


@router.post("/context", response_model=ContextNeedResult)
async def analyze_context_need(
    request: AnalysisRequest,
    llm_service=Depends(get_llm_service),
    prompt_manager=Depends(get_prompt_manager),
    context_manager=Depends(get_context_manager),
):
    analyzer = ContextNeedAnalyzer(llm_service, prompt_manager, context_manager)
    return await analyzer.analyze(request)


@router.post("/emotion", response_model=EmotionalAnalysisResult)
async def analyze_emotion(
    request: AnalysisRequest,
    llm_service=Depends(get_llm_service),
    prompt_manager=Depends(get_prompt_manager),
):
    analyzer = EmotionalAnalyzer(llm_service, prompt_manager)
    return await analyzer.analyze(request)
