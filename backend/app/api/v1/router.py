"""Router agregador de la versión v1 de la API."""

from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    alertas,
    auth,
    health,
    monitoreo,
    notificaciones,
    reportes,
    speedtest,
    tickets,
    ubicaciones,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(ubicaciones.router)
api_router.include_router(tickets.router)
api_router.include_router(notificaciones.router)
api_router.include_router(reportes.router)
api_router.include_router(speedtest.router)
api_router.include_router(monitoreo.router)
api_router.include_router(alertas.router)
