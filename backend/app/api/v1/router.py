from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.auth import router as auth_router
from app.api.v1.backtests import router as backtests_router
from app.api.v1.chat import router as chat_router
from app.api.v1.forecasts import router as forecasts_router
from app.api.v1.health import router as health_router
from app.api.v1.imports import router as imports_router
from app.api.v1.kpi import router as kpi_router
from app.api.v1.news import router as news_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(imports_router)
api_router.include_router(kpi_router)
api_router.include_router(analytics_router)
api_router.include_router(forecasts_router)
api_router.include_router(backtests_router)
api_router.include_router(news_router)
api_router.include_router(chat_router)
