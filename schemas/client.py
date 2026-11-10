"""
Esquemas de clientes para el sistema de agencia SaaS.

Define los modelos Pydantic para la gestión de clientes.
Cada cliente pertenece a un negocio y puede estar asignado a un empleado.
Los estados posibles son: activo, pausado, inactivo.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === Esquema para crear un cliente ===
class ClientCreate(BaseModel):
    """Modelo para registrar un nuevo cliente en el sistema."""

    business_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Nombre del negocio o empresa del cliente",
        examples=["Restaurante El Buen Sabor"]
    )
    contact_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre de la persona de contacto",
        examples=["Juan Pérez"]
    )
    email: str = Field(
        ...,
        description="Correo electrónico de contacto del cliente",
        examples=["juan@buensabor.com"]
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Número de teléfono de contacto",
        examples=["+34 612 345 678"]
    )
    assigned_employee_id: int | None = Field(
        default=None,
        description="ID del empleado asignado a este cliente",
        examples=[1]
    )
    monthly_fee: float = Field(
        default=0.0,
        ge=0,
        description="Tarifa mensual que paga el cliente (debe ser >= 0)",
        examples=[1500.00]
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Notas adicionales sobre el cliente",
        examples=["Cliente premium, requiere atención prioritaria"]
    )

    # Validador para normalizar el email
    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        """Normaliza el email a minúsculas y elimina espacios."""
        return v.strip().lower()

    # Validador para limpiar el nombre del negocio
    @field_validator("business_name")
    @classmethod
    def limpiar_nombre_negocio(cls, v: str) -> str:
        """Elimina espacios extra del nombre del negocio."""
        return v.strip()


# === Esquema para actualizar un cliente ===
# Todos los campos son opcionales para actualizaciones parciales
class ClientUpdate(BaseModel):
    """Modelo para la actualización parcial de un cliente."""

    business_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Nuevo nombre del negocio",
        examples=["Restaurante El Buen Sabor 2.0"]
    )
    contact_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nuevo nombre de contacto",
        examples=["Ana Pérez"]
    )
    email: str | None = Field(
        default=None,
        description="Nuevo correo electrónico",
        examples=["ana@buensabor.com"]
    )
    phone: str | None = Field(
        default=None,
        max_length=20,
        description="Nuevo número de teléfono",
        examples=["+34 698 765 432"]
    )
    status: Literal["activo", "pausado", "inactivo"] | None = Field(
        default=None,
        description="Nuevo estado del cliente",
        examples=["activo"]
    )
    assigned_employee_id: int | None = Field(
        default=None,
        description="ID del nuevo empleado asignado",
        examples=[2]
    )
    monthly_fee: float | None = Field(
        default=None,
        ge=0,
        description="Nueva tarifa mensual (debe ser >= 0)",
        examples=[2000.00]
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Nuevas notas sobre el cliente"
    )

    # Validador: normalizar email si se proporciona
    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str | None) -> str | None:
        """Normaliza el email si se proporciona."""
        if v is not None:
            return v.strip().lower()
        return v


# === Esquema de respuesta del cliente ===
# Incluye todos los campos públicos del cliente
class ClientResponse(BaseModel):
    """Modelo de respuesta con todos los datos públicos del cliente."""

    # Permite crear desde objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único del cliente",
        examples=[1]
    )
    business_name: str = Field(
        ...,
        description="Nombre del negocio o empresa",
        examples=["Restaurante El Buen Sabor"]
    )
    contact_name: str = Field(
        ...,
        description="Nombre de la persona de contacto",
        examples=["Juan Pérez"]
    )
    email: str = Field(
        ...,
        description="Correo electrónico de contacto",
        examples=["juan@buensabor.com"]
    )
    phone: str | None = Field(
        default=None,
        description="Teléfono de contacto",
        examples=["+34 612 345 678"]
    )
    status: str = Field(
        ...,
        description="Estado actual del cliente (activo, pausado, inactivo)",
        examples=["activo"]
    )
    assigned_employee_id: int | None = Field(
        default=None,
        description="ID del empleado asignado",
        examples=[1]
    )
    monthly_fee: float = Field(
        ...,
        description="Tarifa mensual del cliente",
        examples=[1500.00]
    )
    notes: str | None = Field(
        default=None,
        description="Notas adicionales"
    )
    created_at: datetime = Field(
        ...,
        description="Fecha y hora de registro del cliente"
    )
    updated_at: datetime = Field(
        ...,
        description="Fecha y hora de la última actualización"
    )
