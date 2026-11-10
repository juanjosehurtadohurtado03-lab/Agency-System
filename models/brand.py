"""
Modelo de Personalización de Marca (White-Label) de la Agencia.

Permite al dueño de la agencia personalizar completamente la identidad visual:
subir su logo, definir la paleta de colores corporativos (hexadecimal) y
configurar las plantillas base de encabezado y pie de página para los PDFs.
"""

from datetime import datetime
from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class BrandConfig(Base):
    """
    Tabla 'brand_configs': configuración de identidad de la agencia.
    Típicamente existe un único registro activo (Singleton).
    """

    __tablename__ = "brand_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Nombre comercial de la agencia
    agency_name: Mapped[str] = mapped_column(
        String(150),
        default="Mi Agencia Digital",
        nullable=False,
    )

    # Ruta del archivo de logotipo subido (ej: "static/uploads/logos/logo.png")
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Colores corporativos en formato Hex (#RRGGBB)
    primary_color: Mapped[str] = mapped_column(String(7), default="#1E40AF")    # Azul institucional
    secondary_color: Mapped[str] = mapped_column(String(7), default="#3B82F6")  # Azul secundario
    accent_color: Mapped[str] = mapped_column(String(7), default="#10B981")     # Verde acento

    # Color de poder del login del dueño (rojo→negro). Acepta rgb()/hex.
    admin_login_color: Mapped[str] = mapped_column(
        String(30),
        default="rgb(171, 35, 48)",
        nullable=False,
    )

    # Dominio propio del portal del cliente (marca blanca completa, opcional)
    portal_custom_domain: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # Plantillas HTML personalizables para el encabezado y pie de los PDFs generados
    pdf_header_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="""<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid {primary_color}; padding-bottom:10px;">
    <h2>{agency_name}</h2>
    <span>Reporte Oficial de Desempeño</span>
</div>""",
    )

    pdf_footer_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        default="""<div style="text-align:center; font-size:11px; color:#6B7280; border-top:1px solid #E5E7EB; padding-top:10px;">
    {agency_name} &bull; Documento Confidencial &bull; Generado automáticamente
</div>""",
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<BrandConfig id={self.id} agency='{self.agency_name}'>"

