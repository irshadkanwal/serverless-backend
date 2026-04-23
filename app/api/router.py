from fastapi import APIRouter

from app.api.routers import analyze, coaching, health, initiate, knowledge, summary

router = APIRouter()

router.include_router(coaching.router)
router.include_router(health.router)
router.include_router(summary.router)
router.include_router(summary.stage_router)
router.include_router(analyze.router)
router.include_router(knowledge.router)
router.include_router(initiate.router)
