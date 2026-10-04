from fastapi import APIRouter

from app.api.v1 import analytics, areas, auth, dashboard, focuses, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(areas.router)
api_router.include_router(focuses.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
