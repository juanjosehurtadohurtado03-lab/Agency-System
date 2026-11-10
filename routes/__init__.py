"""
Paquete de Enrutadores (Controladores) de la aplicación FastAPI.
"""

from routes.auth import router as auth_router
from routes.brand import router as brand_router
from routes.clients import router as clients_router
from routes.dashboard import router as dashboard_router
from routes.employees import router as employees_router
from routes.financial import router as financial_router
from routes.portal import router as portal_router
from routes.reports import router as reports_router
from routes.settings import router as settings_router

__all__ = [
    "auth_router",
    "clients_router",
    "employees_router",
    "reports_router",
    "brand_router",
    "settings_router",
    "dashboard_router",
    "financial_router",
    "portal_router",
]

