"""
Modelo de Empleado del sistema SaaS.

Representa a los miembros del equipo de la agencia. Cada empleado tiene acceso
limitado a sus propios clientes asignados y puede generar reportes para ellos.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.client import Client
    from models.report import Report


class Employee(Base):
    """
    Tabla 'employees': almacena los empleados de la agencia.
    """

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Nombre completo del empleado
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Correo electrónico institucional (se usa como usuario de login)
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    # Hash de la contraseña del empleado
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Rol en la agencia (ej: "gestor", "analista", "empleado")
    role: Mapped[str] = mapped_column(String(50), default="empleado")

    # Estado del empleado (activo o deshabilitado)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relación: Un empleado tiene múltiples clientes asignados
    clients: Mapped[List["Client"]] = relationship(
        "Client",
        back_populates="assigned_employee",
        lazy="selectin",
    )

    # Relación: Reportes creados por este empleado
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="employee",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name='{self.name}' email='{self.email}'>"

