"""
Dependencias comunes de FastAPI y Seguridad de Sesión.

Maneja la autenticación mediante cookies HTTP-Only y tokens JWT,
así como la verificación de roles (Dueño/Admin vs Empleado).
"""

from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.admin import Admin
from models.brand import BrandConfig
from models.client import Client
from models.employee import Employee
from services.auth_service import decode_access_token


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[Dict[str, Any]]:
    """
    Extrae el token JWT desde la cookie 'access_token' o del encabezado 'Authorization'.
    Si el token es válido, busca en la BD y retorna los datos del usuario.
    Si no hay token o es inválido, devuelve None (sin lanzar excepción).
    """
    token = request.cookies.get("access_token")

    # Si no está en cookie, buscar en Authorization: Bearer <token>
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or not role:
        return None

    # Verificar que el usuario exista en la BD y esté activo
    if role == "admin":
        result = await db.execute(select(Admin).where(Admin.id == int(user_id)))
        admin = result.scalar_one_or_none()
        if admin:
            return {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "role": "admin",
                "is_admin": True,
                "must_change_password": admin.must_change_password,
                "name": f"Admin ({admin.username})",
            }
    elif role == "empleado":
        result = await db.execute(select(Employee).where(Employee.id == int(user_id)))
        emp = result.scalar_one_or_none()
        if emp and emp.is_active:
            return {
                "id": emp.id,
                "username": emp.email,
                "email": emp.email,
                "name": emp.name,
                "role": "empleado",
                "is_admin": False,
                "is_client": False,
                "must_change_password": False,
            }
    elif role == "cliente":
        result = await db.execute(select(Client).where(Client.id == int(user_id)))
        client = result.scalar_one_or_none()
        if client and client.status == "activo" and client.portal_enabled:
            return {
                "id": client.id,
                "username": client.portal_username or client.email,
                "email": client.email,
                "name": client.business_name,
                "contact_name": client.contact_name,
                "role": "cliente",
                "is_admin": False,
                "is_client": True,
                "must_change_password": False,
            }

    return None


async def require_user(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Exige que el usuario sea miembro del equipo (Dueño o Empleado)."""
    if not current_user:
        # Si la petición espera HTML, redirigir a login
        if "text/html" in request.headers.get("accept", "") or request.method == "GET":
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/auth/login"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no iniciada o token inválido.",
        )

    # Si es un cliente intentando entrar al panel interno de la agencia, redirigir a su portal
    if current_user.get("role") == "cliente":
        if "text/html" in request.headers.get("accept", "") or request.method == "GET":
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/portal"},
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido al personal de la agencia.",
        )

    # Bloqueo de seguridad: Si el admin tiene pendiente el cambio forzoso de credenciales iniciales
    if current_user.get("is_admin") and current_user.get("must_change_password"):
        path = request.url.path
        if not path.startswith("/auth/admin/change-credentials") and not path.startswith("/auth/logout"):
            if "text/html" in request.headers.get("accept", "") or request.method == "GET":
                raise HTTPException(
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                    headers={"Location": "/auth/admin/change-credentials"},
                )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cambio obligatorio de credenciales pendiente.",
            )

    return current_user


async def require_client(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Exige que el usuario autenticado sea un cliente en su portal."""
    if not current_user or current_user.get("role") != "cliente":
        if "text/html" in request.headers.get("accept", "") or request.method == "GET":
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/portal/login"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso exclusivo para negocios afiliados.",
        )
    return current_user


async def require_admin(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
) -> Dict[str, Any]:
    """Exige que el usuario autenticado sea el dueño (Admin/Root)."""
    if current_user.get("role") != "admin":
        if "text/html" in request.headers.get("accept", ""):
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": "/auth/admin/login?error=acceso_denegado"},
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido únicamente al dueño de la agencia.",
        )
    return current_user


async def get_active_brand(db: AsyncSession = Depends(get_db)) -> BrandConfig:
    """Obtiene la configuración visual activa de la agencia (o crea una predeterminada)."""
    result = await db.execute(select(BrandConfig).limit(1))
    brand = result.scalar_one_or_none()
    if not brand:
        brand = BrandConfig(
            agency_name="Mi Agencia Digital",
            primary_color="#1E40AF",
            secondary_color="#3B82F6",
            accent_color="#10B981",
        )
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
    return brand

