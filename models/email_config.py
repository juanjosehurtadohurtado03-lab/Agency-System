"""
Modelo de Configuración de Integraciones para Envíos Automáticos.

Permite conectar las credenciales del servidor de correo SMTP (Gmail, Zoho, Mailgun),
la API de SendGrid, o webhooks externos (ej: Make, Zapier, n8n) para disparar
los envíos de reportes a los negocios afiliados.
"""

from datetime import datetime
from sqlalchemy import Boolean, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class EmailConfig(Base):
    """
    Tabla 'email_configs': almacena las credenciales de envío del SaaS.
    Las contraseñas y tokens sensibles se guardan cifrados con clave simétrica.
    """

    __tablename__ = "email_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Proveedor seleccionado: "smtp", "sendgrid" o "webhook"
    provider: Mapped[str] = mapped_column(String(20), default="smtp", nullable=False)

    # --- Configuración SMTP ---
    smtp_host: Mapped[str | None] = mapped_column(String(200), nullable=True)
    smtp_port: Mapped[int] = mapped_column(Integer, default=587, nullable=False)
    smtp_username: Mapped[str | None] = mapped_column(String(200), nullable=True)
    smtp_password_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- Configuración SendGrid ---
    sendgrid_api_key_encrypted: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- Configuración Webhooks (Zapier, Make, n8n) ---
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # --- Remitente visible para los clientes ---
    from_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    from_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Estado de la integración (si está activa para envíos en vivo)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<EmailConfig id={self.id} provider='{self.provider}' active={self.is_active}>"

