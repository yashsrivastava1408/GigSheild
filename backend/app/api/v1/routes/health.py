from fastapi import APIRouter

from app.core.time import utcnow


router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "gigshield-backend",
        "timestamp": utcnow().isoformat(),
    }
