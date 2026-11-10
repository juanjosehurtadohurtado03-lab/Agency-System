"""
Esquemas de reportes para el sistema de agencia SaaS.

Define los modelos Pydantic para la gestión de reportes mensuales
que se generan por cliente. Los reportes tienen un ciclo de vida:
borrador -> enviado -> entregado.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === Esquema para crear un reporte ===
class ReportCreate(BaseModel):
    """Modelo para crear un nuevo reporte mensual de un cliente."""

    client_id: int = Field(
        ...,
        description="ID del cliente al que pertenece el reporte",
        examples=[1]
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Título descriptivo del reporte",
        examples=["Reporte de Redes Sociales - Noviembre 2024"]
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Descripción detallada del contenido del reporte",
        examples=["Análisis de métricas de Instagram y Facebook del mes"]
    )
    period_month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Mes del período del reporte (1-12)",
        examples=[11]
    )
    period_year: int = Field(
        ...,
        ge=2020,
        description="Año del período del reporte (desde 2020)",
        examples=[2024]
    )

    # Validador para limpiar el título
    @field_validator("title")
    @classmethod
    def limpiar_titulo(cls, v: str) -> str:
        """Elimina espacios extra del título."""
        return v.strip()


# === Esquema para actualizar un reporte ===
# Permite cambiar título, descripción y avanzar el estado
class ReportUpdate(BaseModel):
    """Modelo para la actualización parcial de un reporte."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Nuevo título del reporte",
        examples=["Reporte Actualizado - Noviembre 2024"]
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Nueva descripción del reporte"
    )
    status: Literal["borrador", "enviado", "entregado"] | None = Field(
        default=None,
        description="Nuevo estado del reporte en su ciclo de vida",
        examples=["enviado"]
    )

    # Validador para limpiar el título si se proporciona
    @field_validator("title")
    @classmethod
    def limpiar_titulo(cls, v: str | None) -> str | None:
        """Limpia el título si se proporciona."""
        if v is not None:
            return v.strip()
        return v


# === Esquema de respuesta del reporte ===
# Incluye todos los campos del reporte incluyendo metadatos de tiempo
class ReportResponse(BaseModel):
    """Modelo de respuesta con todos los datos del reporte."""

    # Permite crear desde objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único del reporte",
        examples=[1]
    )
    client_id: int = Field(
        ...,
        description="ID del cliente asociado",
        examples=[1]
    )
    title: str = Field(
        ...,
        description="Título del reporte",
        examples=["Reporte de Redes Sociales - Noviembre 2024"]
    )
    description: str | None = Field(
        default=None,
        description="Descripción del contenido del reporte"
    )
    period_month: int = Field(
        ...,
        description="Mes del período (1-12)",
        examples=[11]
    )
    period_year: int = Field(
        ...,
        description="Año del período",
        examples=[2024]
    )
    status: str = Field(
        ...,
        description="Estado actual del reporte (borrador, enviado, entregado)",
        examples=["borrador"]
    )
    created_at: datetime = Field(
        ...,
        description="Fecha y hora de creación del reporte"
    )
    sent_at: datetime | None = Field(
        default=None,
        description="Fecha y hora en que se envió el reporte al cliente"
    )
