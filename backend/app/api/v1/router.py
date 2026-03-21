from fastapi import APIRouter

from app.api.v1.routes import admin
from app.api.v1.routes import auth
from app.api.v1.routes import claims
from app.api.v1.routes import disruptions
from app.api.v1.routes import health
from app.api.v1.routes import internal
from app.api.v1.routes import payments
from app.api.v1.routes import policies
from app.api.v1.routes import premium
from app.api.v1.routes import workers


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(premium.router, prefix="/premium", tags=["premium"])
api_router.include_router(workers.router, prefix="/workers", tags=["workers"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(disruptions.router, prefix="/disruptions", tags=["disruptions"])
api_router.include_router(claims.router, prefix="/claims", tags=["claims"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
