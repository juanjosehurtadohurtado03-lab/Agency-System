"""
Modelo de Negocio Afiliado / Cliente de la Agencia.

Los clientes son los negocios para los cuales la agencia presta servicios y
genera reportes periódicos. El dueño (admin) tiene permisos totales para
crear, editar, pausar y eliminar estos negocios, así como asignarles empleados responsables.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.employee import Employee
    from models.report import Report
    from models.financial import FinancialRecord
    from models.task import Task


class Client(Base):
    """
    Tabla 'clients': almacena negocios afiliados a la agencia.
    """

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Nombre comercial o razón social del negocio
    business_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)

    # Persona de contacto principal en el negocio
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Correo para enviar los reportes automáticos
    email: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Teléfono de contacto
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Estado del negocio afiliado:
    # - "activo": servicio regular, genera reportes
    # - "pausado": servicio suspendido temporalmente por el dueño
    # - "inactivo": dado de baja (soft-delete)
    status: Mapped[str] = mapped_column(String(20), default="activo", nullable=False)

    # Empleado específico asignado a este cliente
    assigned_employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Cuota mensual que paga este cliente a la agencia
    monthly_fee: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # --- Credenciales para el Portal Exclusivo del Cliente ---
    # Usuario del cliente (por defecto se autogenera con su negocio o correo)
    portal_username: Mapped[str | None] = mapped_column(
        String(60),
        unique=True,
        index=True,
        nullable=True,
    )

    # Código especial de acceso enviado por correo (ej: CLI-74829)
    portal_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Si el acceso al portal del cliente está habilitado
    portal_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Notas internas o acuerdos especiales
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # --- Relaciones ORM ---
    assigned_employee: Mapped["Employee | None"] = relationship(
        "Employee",
        back_populates="clients",
        lazy="selectin",
    )

    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    financial_records: Mapped[List["FinancialRecord"]] = relationship(
        "FinancialRecord",
        back_populates="client",
        lazy="selectin",
    )

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Task.is_done, Task.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Client id={self.id} business='{self.business_name}' status='{self.status}'>"

