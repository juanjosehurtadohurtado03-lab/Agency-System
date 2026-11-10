"""
Esquemas de autenticación para el sistema de agencia SaaS.

Define los modelos Pydantic para las peticiones y respuestas
relacionadas con el login y los tokens JWT.
"""

from pydantic import BaseModel, Field


# === Esquema de petición de login ===
# El cliente envía usuario y contraseña para autenticarse
class LoginRequest(BaseModel):
    """Modelo para la solicitud de inicio de sesión."""

    username: str = Field(
        ...,
        min_length=1,
        description="Nombre de usuario del administrador",
        examples=["admin"]
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Contraseña del usuario",
        examples=["mi_password_seguro"]
    )


# === Esquema de respuesta con token ===
# Después de un login exitoso, se devuelve el token de acceso
class TokenResponse(BaseModel):
    """Modelo de respuesta con el token JWT generado."""

    access_token: str = Field(
        ...,
        description="Token JWT de acceso generado tras autenticación exitosa",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token, siempre 'bearer' para JWT",
        examples=["bearer"]
    )


# === Datos extraídos del token ===
# Se usa internamente para decodificar y transportar los datos del token JWT
class TokenData(BaseModel):
    """Modelo interno para los datos decodificados del token JWT."""

    username: str | None = Field(
        default=None,
        description="Nombre de usuario extraído del token"
    )
    role: str | None = Field(
        default=None,
        description="Rol del usuario (ej: 'admin', 'empleado')"
    )
