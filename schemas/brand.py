"""
Esquemas de personalización de marca (branding) para el sistema de agencia SaaS.

Define los modelos Pydantic para gestionar la identidad visual de la agencia:
colores, nombre, y plantillas HTML para la generación de PDFs.
Cada agencia puede personalizar su apariencia en el sistema.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
import re


# === Esquema para actualizar la configuración de marca ===
# Todos los campos son opcionales para permitir actualizaciones parciales
class BrandUpdate(BaseModel):
    """Modelo para actualizar la configuración de marca de la agencia."""

    agency_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Nombre de la agencia que se muestra en la interfaz",
        examples=["Agencia Digital Creativa"]
    )
    primary_color: str | None = Field(
        default=None,
        max_length=7,
        description="Color primario en formato hexadecimal (#RRGGBB)",
        examples=["#2563EB"]
    )
    secondary_color: str | None = Field(
        default=None,
        max_length=7,
        description="Color secundario en formato hexadecimal (#RRGGBB)",
        examples=["#1E40AF"]
    )
    accent_color: str | None = Field(
        default=None,
        max_length=7,
        description="Color de acento para elementos destacados (#RRGGBB)",
        examples=["#F59E0B"]
    )
    pdf_header_html: str | None = Field(
        default=None,
        max_length=5000,
        description="HTML personalizado para el encabezado de PDFs generados",
        examples=["<div style='text-align:center'><h1>Mi Agencia</h1></div>"]
    )
    pdf_footer_html: str | None = Field(
        default=None,
        max_length=5000,
        description="HTML personalizado para el pie de página de PDFs generados",
        examples=["<p style='text-align:center'>© 2024 Mi Agencia</p>"]
    )

    # Validador para verificar formato de colores hexadecimales
    @field_validator("primary_color", "secondary_color", "accent_color")
    @classmethod
    def validar_color_hex(cls, v: str | None) -> str | None:
        """
        Valida que el color esté en formato hexadecimal correcto (#RRGGBB).
        Acepta formatos de 3 o 6 dígitos (ej: #FFF o #FFFFFF).
        """
        if v is not None:
            # Patrón regex para colores hex: # seguido de 3 o 6 caracteres hex
            patron = r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"
            if not re.match(patron, v):
                raise ValueError(
                    f"El color '{v}' no es un formato hexadecimal válido. "
                    "Use el formato #RGB o #RRGGBB (ej: #FFF o #FFFFFF)"
                )
            # Normalizar a mayúsculas para consistencia
            return v.upper()
        return v


# === Esquema de respuesta de marca ===
# Devuelve toda la configuración visual de la agencia
class BrandResponse(BaseModel):
    """Modelo de respuesta con la configuración completa de marca."""

    # Permite crear desde objetos ORM de SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(
        ...,
        description="Identificador único de la configuración de marca",
        examples=[1]
    )
    agency_name: str = Field(
        ...,
        description="Nombre de la agencia",
        examples=["Agencia Digital Creativa"]
    )
    primary_color: str = Field(
        ...,
        description="Color primario de la marca",
        examples=["#2563EB"]
    )
    secondary_color: str = Field(
        ...,
        description="Color secundario de la marca",
        examples=["#1E40AF"]
    )
    accent_color: str = Field(
        ...,
        description="Color de acento de la marca",
        examples=["#F59E0B"]
    )
    pdf_header_html: str | None = Field(
        default=None,
        description="HTML del encabezado de PDFs"
    )
    pdf_footer_html: str | None = Field(
        default=None,
        description="HTML del pie de página de PDFs"
    )
