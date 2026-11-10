"""
Esquemas financieros para el sistema de agencia SaaS.

Define los modelos Pydantic para gestionar registros financieros
(ingresos y gastos), así como resúmenes financieros con totales
y desglose por categoría.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === Esquema para crear un registro financiero ===
class FinancialCreate(BaseModel):
    """Modelo para registrar un nuevo movimiento financiero (ingreso o gasto)."""

    type: Literal["ingreso", "gasto"] = Field(
        ...,
        description="Tipo de movimiento: 'ingreso' para entradas, 'gasto' para salidas",
        examples=["ingreso"]
    )
    amount: float = Field(
        ...,
        gt=0,
        description="Monto del movimiento (debe ser mayor a 0)",
        examples=[1500.00]
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Descripción del movimiento financiero",
        examples=["Pago mensual de cliente - Restaurante El Buen Sabor"]
    )
    category: str | None = Field(
        default=None,
        max_length=100,
        description="Categoría del movimiento para clasificación",
        examples=["servicios", "publicidad", "nómina", "herramientas"]
    )
    client_id: int | None = Field(
        default=None,
        description="ID del cliente asociado (si aplica, para vincular ingresos)",
        examples=[1]
    )
    record_date: date = Field(
        ...,
        description="Fecha del movimiento financiero",
        examples=["2024-11-15"]
    )

    # Validador para limpiar la descripción
    @field_validator("description")
    @classmethod
    def limpiar_descripcion(cls, v: str) -> str:
        """Elimina espacios extra de la descripción."""
        return v.strip()

    # Validador para normalizar la categoría
    @field_validator("category")
    @classmethod
    def normalizar_categoria(cls, v: str | None) -> str | None:
        """Normaliza la categoría a minúsculas si se proporciona."""
        if v is not None:
            return v.strip().lower()
        return v


# === Esquema de respuesta de registro financiero ===
class FinancialResponse(BaseModel):
    """Modelo de respuesta con los datos completos del registro financiero."""

    # Permite crear desde objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único del registro",
        examples=[1]
    )
    type: str = Field(
        ...,
        description="Tipo de movimiento (ingreso o gasto)",
        examples=["ingreso"]
    )
    amount: float = Field(
        ...,
        description="Monto del movimiento",
        examples=[1500.00]
    )
    description: str = Field(
        ...,
        description="Descripción del movimiento",
        examples=["Pago mensual de cliente"]
    )
    category: str | None = Field(
        default=None,
        description="Categoría del movimiento",
        examples=["servicios"]
    )
    client_id: int | None = Field(
        default=None,
        description="ID del cliente asociado",
        examples=[1]
    )
    record_date: date = Field(
        ...,
        description="Fecha del movimiento",
        examples=["2024-11-15"]
    )
    created_at: date = Field(
        ...,
        description="Fecha de creación del registro en el sistema"
    )


# === Esquema de resumen financiero ===
# Modelo calculado que agrega totales de ingresos, gastos y balance
class FinancialSummary(BaseModel):
    """
    Modelo de resumen financiero con totales agregados.
    
    Este modelo no proviene directamente de la base de datos,
    sino que se calcula a partir de los registros financieros.
    """

    total_ingresos: float = Field(
        ...,
        description="Suma total de todos los ingresos en el período",
        examples=[25000.00]
    )
    total_gastos: float = Field(
        ...,
        description="Suma total de todos los gastos en el período",
        examples=[15000.00]
    )
    balance: float = Field(
        ...,
        description="Diferencia entre ingresos y gastos (ganancia o pérdida)",
        examples=[10000.00]
    )
    by_category: dict[str, float] = Field(
        ...,
        description="Desglose de montos agrupados por categoría",
        examples=[{
            "servicios": 20000.00,
            "publicidad": 5000.00,
            "nómina": 10000.00,
            "herramientas": 2000.00
        }]
    )
