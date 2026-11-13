"""
Modelo de Tareas / Checklist Operativo por Cliente.

Permite a la agencia llevar un control rápido de las tareas pendientes de cada
negocio afiliado (ej: "Diseñar creativos", "Revisar pauta", "Enviar reporte"),
resolviendo el caos operativo típico de las agencias pequeñas.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.client import Client


class Task(Base):
    """
    Tabla 'tasks': tareas operativas semanales vinculadas a un cliente.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Cliente al que pertenece la tarea
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Descripción breve de la tarea
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # Detalle opcional
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ¿Completada?
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Fecha límite opcional (semana)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relación ORM
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title='{self.title}' done={self.is_done}>"
