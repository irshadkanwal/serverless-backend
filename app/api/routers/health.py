from fastapi import APIRouter, HTTPException

from app.services.db.file_db_service import FileDatabaseService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Check database connectivity"""
    try:
        db = FileDatabaseService()
        async with db.get_connection() as conn:
            _ = await conn.fetchval("SELECT 1")
            return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail={"status": "unhealthy", "database": str(e)}
        )
