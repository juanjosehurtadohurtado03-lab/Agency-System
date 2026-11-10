"""
Esquemas de empleados para el sistema de agencia SaaS.

Define los modelos Pydantic para gestionar empleados de la agencia.
Los empleados pueden tener clientes asignados y diferentes roles.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Importación condicional para evitar referencias circulares
# TYPE_CHECKING solo es True durante el análisis estático, no en ejecución
if TYPE_CHECKING:
    pass


# === Esquema para crear un empleado ===
class EmployeeCreate(BaseModel):
    """Modelo para registrar un nuevo empleado en el sistema."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre completo del empleado",
        examples=["María García López"]
    )
    email: str = Field(
        ...,
        description="Correo electrónico corporativo del empleado",
        examples=["maria.garcia@agencia.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contraseña de acceso (mínimo 8 caracteres)",
        examples=["Empl0y33_P@ss!"]
    )
    role: str = Field(
        default="empleado",
        description="Rol del empleado dentro de la agencia",
        examples=["empleado", "gerente", "diseñador"]
    )

    # Validador para normalizar el email a minúsculas
    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        """Normaliza el email eliminando espacios y convirtiendo a minúsculas."""
        return v.strip().lower()

    # Validador para limpiar el nombre
    @field_validator("name")
    @classmethod
    def limpiar_nombre(cls, v: str) -> str:
        """Elimina espacios extra del nombre."""
        return v.strip()


# === Esquema para actualizar un empleado ===
# Todos los campos son opcionales para permitir actualizaciones parciales (PATCH)
class EmployeeUpdate(BaseModel):
    """Modelo para la actualización parcial de un empleado."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nuevo nombre del empleado",
        examples=["María García Fernández"]
    )
    email: str | None = Field(
        default=None,
        description="Nuevo correo electrónico",
        examples=["maria.garcia.nuevo@agencia.com"]
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Nueva contraseña (mínimo 8 caracteres si se proporciona)"
    )
    role: str | None = Field(
        default=None,
        description="Nuevo rol del empleado",
        examples=["gerente"]
    )
    is_active: bool | None = Field(
        default=None,
        description="Estado activo/inactivo del empleado"
    )

    # Validador: normalizar email si se proporciona
    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str | None) -> str | None:
        """Normaliza el email si se proporciona."""
        if v is not None:
            return v.strip().lower()
        return v


# === Esquema de respuesta del empleado ===
# Excluye la contraseña y datos sensibles
class EmployeeResponse(BaseModel):
    """Modelo de respuesta con los datos públicos del empleado."""

    # Permite crear instancias desde objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único del empleado",
        examples=[1]
    )
    name: str = Field(
        ...,
        description="Nombre completo del empleado",
        examples=["María García López"]
    )
    email: str = Field(
        ...,
        description="Correo electrónico del empleado",
        examples=["maria.garcia@agencia.com"]
    )
    role: str = Field(
        ...,
        description="Rol del empleado en la agencia",
        examples=["empleado"]
    )
    is_active: bool = Field(
        ...,
        description="Indica si el empleado está activo en el sistema",
        examples=[True]
    )
    created_at: datetime = Field(
        ...,
        description="Fecha y hora de registro del empleado"
    )


# === Esquema extendido: empleado con sus clientes ===
# Hereda de EmployeeResponse y añade la lista de clientes asignados
class EmployeeWithClients(EmployeeResponse):
    """Modelo de respuesta del empleado incluyendo sus clientes asignados."""

    # Importamos ClientResponse aquí para evitar dependencia circular
    # La lista puede estar vacía si el empleado no tiene clientes asignados
    clients: list["ClientResponse"] = Field(
        default_factory=list,
        description="Lista de clientes asignados a este empleado"
    )


# Importación diferida para resolver la referencia adelantada (forward reference)
# Esto permite que EmployeeWithClients use ClientResponse sin importación circular
from schemas.client import ClientResponse  # noqa: E402

# Reconstruir el modelo para resolver las referencias adelantadas
EmployeeWithClients.model_rebuild()
