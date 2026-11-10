"""
Paquete de modelos ORM de SQLAlchemy.

Exporta todos los modelos de la base de datos para que SQLAlchemy
los detecte automáticamente durante la inicialización de las tablas.
"""

from database import Base
from models.admin import Admin
from models.brand import BrandConfig
from models.client import Client
from models.email_config import EmailConfig
from models.employee import Employee
from models.financial import FinancialRecord
from models.report import Report

__all__ = [
    "Base",
    "Admin",
    "Employee",
    "Client",
    "Report",
    "BrandConfig",
    "EmailConfig",
    "FinancialRecord",
]

