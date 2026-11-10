"""
Esquemas de configuración de email para el sistema de agencia SaaS.

Define los modelos Pydantic para gestionar la configuración del servicio
de correo electrónico. Soporta dos proveedores: SMTP directo y SendGrid.
IMPORTANTE: Las contraseñas y API keys nunca se exponen en las respuestas.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# === Esquema para actualizar la configuración de email ===
# Permite cambiar entre proveedores SMTP y SendGrid
class EmailConfigUpdate(BaseModel):
    """Modelo para actualizar la configuración del servicio de email."""

    provider: Literal["smtp", "sendgrid"] | None = Field(
        default=None,
        description="Proveedor de email: 'smtp' para servidor propio o 'sendgrid' para API",
        examples=["smtp"]
    )
    smtp_host: str | None = Field(
        default=None,
        max_length=255,
        description="Dirección del servidor SMTP",
        examples=["smtp.gmail.com"]
    )
    smtp_port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description="Puerto del servidor SMTP (comúnmente 587 para TLS, 465 para SSL)",
        examples=[587]
    )
    smtp_username: str | None = Field(
        default=None,
        max_length=255,
        description="Usuario para autenticación SMTP",
        examples=["noreply@agencia.com"]
    )
    smtp_password: str | None = Field(
        default=None,
        max_length=255,
        description="Contraseña para autenticación SMTP (se almacena encriptada)"
    )
    sendgrid_api_key: str | None = Field(
        default=None,
        max_length=255,
        description="API Key de SendGrid (se almacena encriptada)"
    )
    from_email: str | None = Field(
        default=None,
        max_length=255,
        description="Dirección de correo del remitente",
        examples=["reportes@agencia.com"]
    )
    from_name: str | None = Field(
        default=None,
        max_length=100,
        description="Nombre del remitente que aparece en los correos",
        examples=["Agencia Digital"]
    )
    is_active: bool | None = Field(
        default=None,
        description="Indica si el servicio de email está habilitado"
    )

    # Validador para normalizar el email del remitente
    @field_validator("from_email")
    @classmethod
    def normalizar_from_email(cls, v: str | None) -> str | None:
        """Normaliza el email del remitente a minúsculas."""
        if v is not None:
            return v.strip().lower()
        return v


# === Esquema de respuesta de configuración de email ===
# SEGURIDAD: No incluye smtp_password ni sendgrid_api_key
# para evitar exponer credenciales sensibles en la API
class EmailConfigResponse(BaseModel):
    """
    Modelo de respuesta con la configuración de email.
    
    NOTA DE SEGURIDAD: Las contraseñas y API keys se excluyen
    intencionalmente de la respuesta para proteger credenciales.
    """

    # Permite crear desde objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único de la configuración",
        examples=[1]
    )
    provider: str = Field(
        ...,
        description="Proveedor de email activo (smtp o sendgrid)",
        examples=["smtp"]
    )
    smtp_host: str | None = Field(
        default=None,
        description="Servidor SMTP configurado",
        examples=["smtp.gmail.com"]
    )
    smtp_port: int | None = Field(
        default=None,
        description="Puerto SMTP configurado",
        examples=[587]
    )
    smtp_username: str | None = Field(
        default=None,
        description="Usuario SMTP configurado",
        examples=["noreply@agencia.com"]
    )
    # NOTA: smtp_password NO se incluye por seguridad
    # NOTA: sendgrid_api_key NO se incluye por seguridad
    from_email: str | None = Field(
        default=None,
        description="Dirección de correo del remitente",
        examples=["reportes@agencia.com"]
    )
    from_name: str | None = Field(
        default=None,
        description="Nombre del remitente",
        examples=["Agencia Digital"]
    )
    is_active: bool = Field(
        ...,
        description="Indica si el servicio de email está habilitado",
        examples=[True]
    )
