"""
Modelo de Reporte Automático generado para los clientes afiliados.

Almacena los informes generados por empleados o automáticamente por el SaaS,
su estado de envío, período al que corresponde y ruta del archivo PDF generado.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.client import Client
    from models.employee import Employee


class Report(Base):
    """
    Tabla 'reports': almacena los reportes de rendimiento o estado de clientes.
    """

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Cliente al que pertenece el reporte
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Empleado que elaboró o gestiona el reporte
    employee_id: Mapped[int | None] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Título descriptivo (ej: "Reporte Mensual de Marketing - Octubre 2026")
    title: Mapped[str] = mapped_column(String(200), nullable=False)

    # Resumen ejecutivo o comentarios del analista
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Ruta física al archivo PDF generado con el branding de la agencia
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Estado del reporte:
    # - "borrador": en elaboración
    # - "enviado": enviado por correo/webhook al cliente
    # - "entregado": confirmado recibido
    status: Mapped[str] = mapped_column(String(20), default="borrador", nullable=False)

    # Período que abarca el reporte
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Métricas consolidadas en formato JSON serializado (leads, clics, ventas, ROI, etc.)
    metrics_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Campos estructurados básicos de desempeño ---
    # Inversión publicitaria del período (semana/mes) en la moneda de la agencia
    investment: Mapped[float | None] = mapped_column(Float, nullable=True, default=0.0)
    # Resultados obtenidos: leads / contactos / conversiones
    leads: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    # Estado de la campaña: activa | optimizacion | pausada | finalizada
    campaign_status: Mapped[str | None] = mapped_column(String(30), nullable=True, default="activa")

    # Fecha en que se realizó el envío automático
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )

    # --- Relaciones ORM ---
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="reports",
        lazy="selectin",
    )

    employee: Mapped["Employee | None"] = relationship(
        "Employee",
        back_populates="reports",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Report id={self.id} title='{self.title}' status='{self.status}'>"

