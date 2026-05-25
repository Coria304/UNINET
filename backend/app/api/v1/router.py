"""Router agregador de la versión v1 de la API."""

from fastapi import APIRouter

from app.api.v1.routes import admin, auth, health, tickets, ubicaciones

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(ubicaciones.router)
api_router.include_router(tickets.router)
