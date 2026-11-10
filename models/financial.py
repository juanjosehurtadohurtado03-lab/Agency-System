"""
Modelo de Registro Financiero del sistema.

Los registros financieros permiten llevar un control de los ingresos
y gastos de la agencia. Pueden estar asociados a un cliente específico
(por ejemplo, el pago mensual de un cliente) o ser gastos generales.
"""

from datetime import date, datetime

from sqlalchemy import Date, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# --- Prevención de importaciones circulares ---
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.client import Client


class FinancialRecord(Base):
    """
    Tabla 'financial_records': registros de ingresos y gastos.

    Tipos de registro:
    - ingreso: dinero que entra (pagos de clientes, otros ingresos)
    - gasto: dinero que sale (sueldos, herramientas, publicidad, etc.)

    Cada registro puede asociarse opcionalmente a un cliente para
    saber qué ingresos genera cada uno.
    """

    # --- Nombre de la tabla en la base de datos ---
    __tablename__ = "financial_records"

    # --- Columnas ---

    # Identificador único, autoincremental
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    # Tipo de registro: "ingreso" o "gasto"
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Monto del registro (siempre positivo, el tipo indica si es ingreso o gasto)
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Descripción del movimiento financiero
    description: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )

    # Categoría del registro (ej: "sueldo", "herramientas", "publicidad")
    # Permite agrupar y filtrar registros por categoría
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        default=None,
    )

    # Cliente asociado al registro (opcional)
    # Útil para vincular pagos de clientes con sus registros financieros
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("clients.id"),
        nullable=True,
        default=None,
    )

    # Fecha del movimiento financiero (no necesariamente la fecha de creación)
    record_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Fecha de creación del registro en el sistema
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )

    # --- Relaciones ORM ---

    # Relación con el cliente asociado (muchos-a-uno, opcional)
    client: Mapped["Client | None"] = relationship(
        "Client",
        back_populates="financial_records",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """Representación legible del registro financiero."""
        return (
            f"<FinancialRecord(id={self.id}, type='{self.type}', "
            f"amount={self.amount}, date='{self.record_date}')>"
        )
