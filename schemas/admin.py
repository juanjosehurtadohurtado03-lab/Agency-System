"""
Esquemas de administrador para el sistema de agencia SaaS.

Define los modelos Pydantic para crear, actualizar y representar
administradores del sistema. Solo los superadmins pueden gestionar
otros administradores.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === Esquema para crear un administrador ===
# Validamos longitud mínima de usuario y contraseña por seguridad
class AdminCreate(BaseModel):
    """Modelo para la creación de un nuevo administrador."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nombre de usuario único del administrador (mínimo 3 caracteres)",
        examples=["admin_principal"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Contraseña segura (mínimo 8 caracteres)",
        examples=["Str0ng_P@ssw0rd!"]
    )
    email: str = Field(
        ...,
        description="Correo electrónico del administrador",
        examples=["admin@agencia.com"]
    )

    # Validador para normalizar el email a minúsculas
    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        """Convierte el email a minúsculas para consistencia."""
        return v.strip().lower()

    # Validador para limpiar espacios del username
    @field_validator("username")
    @classmethod
    def normalizar_username(cls, v: str) -> str:
        """Elimina espacios en blanco al inicio y final del username."""
        return v.strip()


# === Esquema para actualizar un administrador ===
# Todos los campos son opcionales; solo se actualizan los enviados
class AdminUpdate(BaseModel):
    """Modelo para la actualización parcial de un administrador."""

    email: str | None = Field(
        default=None,
        description="Nuevo correo electrónico",
        examples=["nuevo_email@agencia.com"]
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Nueva contraseña (mínimo 8 caracteres si se proporciona)",
        examples=["NuevoP@ss2024!"]
    )

    # Validador: si se envía email, normalizarlo
    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str | None) -> str | None:
        """Convierte el email a minúsculas si se proporciona."""
        if v is not None:
            return v.strip().lower()
        return v


# === Esquema de respuesta del administrador ===
# Nunca exponemos la contraseña en las respuestas de la API
class AdminResponse(BaseModel):
    """Modelo de respuesta con los datos públicos del administrador."""

    # Configuración de Pydantic v2 para permitir crear el schema
    # desde objetos ORM de SQLAlchemy (from_attributes=True)
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único del administrador",
        examples=[1]
    )
    username: str = Field(
        ...,
        description="Nombre de usuario del administrador",
        examples=["admin_principal"]
    )
    email: str = Field(
        ...,
        description="Correo electrónico del administrador",
        examples=["admin@agencia.com"]
    )
    created_at: datetime = Field(
        ...,
        description="Fecha y hora de creación del registro"
    )
