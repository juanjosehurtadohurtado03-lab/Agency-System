"""
Paquete de Esquemas de Pydantic v2.

Define modelos de validación para solicitudes (Requests) y respuestas (Responses)
garantizando la integridad de los datos que entran y salen de la API.
"""

from schemas.admin import AdminCreate, AdminResponse, AdminUpdate
from schemas.auth import LoginRequest, TokenData, TokenResponse
from schemas.brand import BrandResponse, BrandUpdate
from schemas.client import ClientCreate, ClientResponse, ClientUpdate
from schemas.dashboard import ClientStatusSummary, DashboardStats, MonthlyReportCount
from schemas.email_config import EmailConfigResponse, EmailConfigUpdate
from schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
    EmployeeWithClients,
)
from schemas.financial import (
    FinancialCreate,
    FinancialResponse,
    FinancialSummary,
)
from schemas.report import ReportCreate, ReportResponse, ReportUpdate

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "TokenData",
    "AdminCreate",
    "AdminUpdate",
    "AdminResponse",
    "EmployeeCreate",
    "EmployeeUpdate",
    "EmployeeResponse",
    "EmployeeWithClients",
    "ClientCreate",
    "ClientUpdate",
    "ClientResponse",
    "ReportCreate",
    "ReportUpdate",
    "ReportResponse",
    "BrandUpdate",
    "BrandResponse",
    "EmailConfigUpdate",
    "EmailConfigResponse",
    "FinancialCreate",
    "FinancialResponse",
    "FinancialSummary",
    "DashboardStats",
    "MonthlyReportCount",
    "ClientStatusSummary",
]

