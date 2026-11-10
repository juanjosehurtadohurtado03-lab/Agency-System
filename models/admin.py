"""
Modelo del Administrador / Dueño de la Agencia.

Este modelo representa al usuario raíz (admin/root) que tiene control total
sobre el SaaS: puede editar, pausar y eliminar clientes afiliados, gestionar
empleados, personalizar la marca y configurar las integraciones.
"""

from datetime import datetime
from sqlalchemy import Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Admin(Base):
    """
    Tabla 'admins': almacena las credenciales del dueño de la agencia.
    La clave se guarda de manera irreversible con hash seguro (bcrypt).
    """

    __tablename__ = "admins"

    # Identificador único
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Nombre de usuario único para el login del jefe
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    # Nombres y Apellidos completos del CEO / Dueño
    full_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # Documento de identidad (Cédula, DNI o RIF)
    document_id: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # Teléfono de contacto directo del Dueño
    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # Hash seguro de la contraseña especial asignada por el dueño
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Correo de contacto y notificaciones del dueño
    email: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Indicador de primer inicio: Si es True, el sistema exige cambio inmediato de usuario y contraseña
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps para auditoría
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Admin id={self.id} username='{self.username}'>"

