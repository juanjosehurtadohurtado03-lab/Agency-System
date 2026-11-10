"""
Rutas de Autenticación y Control de Acceso.

Maneja:
1. Login exclusivo para el dueño (Admin/Root) con su usuario y contraseña encriptada.
2. Login para el equipo/empleados de la agencia.
3. Asistente de configuración inicial (Setup) para crear el primer usuario dueño.
4. Cierre de sesión seguro con limpieza de cookies.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.admin import Admin
from models.brand import BrandConfig
from models.employee import Employee
from routes.deps import get_active_brand, get_current_user_optional, require_admin
from services.auth_service import (
    create_access_token,
    hash_password,
    validate_strong_password,
    verify_password,
)
from templates_engine import templates

router = APIRouter(prefix="/auth", tags=["Autenticación"])


# ==============================================================================
# ASISTENTE DE PRIMERA VEZ (SETUP INICIAL DEL JEFE DE LA AGENCIA)
# ==============================================================================

@router.get("/setup", response_class=HTMLResponse)
async def setup_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra la pantalla de configuración inicial si no existe ningún admin aún."""
    result = await db.execute(select(Admin).limit(1))
    existing_admin = result.scalar_one_or_none()
    if existing_admin:
        # Ya existe un admin, redirigir al login exclusivo del dueño
        return RedirectResponse(url="/auth/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "auth/setup.html",
        {"request": request, "brand": brand, "error": None},
    )


@router.post("/setup")
async def setup_admin(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    email: str = Form(...),
    agency_name: str = Form("Mi Agencia"),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Registra al dueño de la agencia con su contraseña encriptada."""
    result = await db.execute(select(Admin).limit(1))
    if result.scalar_one_or_none():
        return RedirectResponse(url="/auth/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    if password != confirm_password:
        return templates.TemplateResponse(
            "auth/setup.html",
            {"request": request, "brand": brand, "error": "Las contraseñas no coinciden."},
            status_code=400,
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            "auth/setup.html",
            {"request": request, "brand": brand, "error": "La contraseña debe tener al menos 6 caracteres."},
            status_code=400,
        )

    # 1. Encriptar la contraseña con bcrypt
    hashed_pwd = hash_password(password)

    # 2. Guardar al Dueño
    new_admin = Admin(
        username=username.strip(),
        password_hash=hashed_pwd,
        email=email.strip().lower(),
    )
    db.add(new_admin)

    # 3. Guardar el nombre de la agencia
    brand.agency_name = agency_name.strip()

    await db.commit()
    await db.refresh(new_admin)

    # Iniciar sesión inmediatamente creando el token JWT
    token = create_access_token(data={"sub": str(new_admin.id), "role": "admin"})

    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 8,  # 8 horas
        samesite="lax",
    )
    return response


# ==============================================================================
# LOGIN EXCLUSIVO PARA EL DUEÑO DE LA AGENCIA (ADMIN/ROOT)
# ==============================================================================

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Pantalla de acceso reservada para el jefe de la agencia."""
    # Verificar si existe al menos un admin, si no, guiar al setup
    result = await db.execute(select(Admin).limit(1))
    if not result.scalar_one_or_none():
        return RedirectResponse(url="/auth/setup", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "auth/admin_login.html",
        {"request": request, "brand": brand, "error": request.query_params.get("error")},
    )


@router.post("/admin/login")
async def admin_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Valida las credenciales del dueño y genera la sesión administrativa."""
    result = await db.execute(select(Admin).where(Admin.username == username.strip()))
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "auth/admin_login.html",
            {
                "request": request,
                "brand": brand,
                "error": "Usuario o clave administrativa incorrecta.",
            },
            status_code=401,
        )

    token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    # Si es el primer inicio y tiene pendiente el cambio obligatorio de usuario y clave:
    next_url = "/auth/admin/change-credentials" if admin.must_change_password else "/dashboard"

    response = RedirectResponse(url=next_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 8,
        samesite="lax",
    )
    return response


# ==============================================================================
# CAMBIO OBLIGATORIO DE CREDENCIALES DEL DUEÑO (ALTA SEGURIDAD)
# ==============================================================================

@router.get("/admin/change-credentials", response_class=HTMLResponse)
async def change_credentials_page(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Pantalla obligatoria para cambiar usuario y contraseña inicial."""
    if not current_user or not current_user.get("is_admin"):
        return RedirectResponse(url="/auth/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "auth/change_credentials.html",
        {
            "request": request,
            "current_user": current_user,
            "brand": brand,
            "error": None,
        },
    )


@router.post("/admin/change-credentials")
async def change_credentials_post(
    request: Request,
    new_username: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Procesa el cambio obligatorio de credenciales con validación de alta seguridad."""
    if not current_user or not current_user.get("is_admin"):
        return RedirectResponse(url="/auth/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    clean_username = new_username.strip()

    # 1. Validar nombre de usuario
    if len(clean_username) < 4:
        return templates.TemplateResponse(
            "auth/change_credentials.html",
            {
                "request": request,
                "current_user": current_user,
                "brand": brand,
                "error": "El nombre de usuario debe tener al menos 4 caracteres.",
            },
            status_code=400,
        )

    # 2. Validar coincidencia de contraseña
    if new_password != confirm_password:
        return templates.TemplateResponse(
            "auth/change_credentials.html",
            {
                "request": request,
                "current_user": current_user,
                "brand": brand,
                "error": "La nueva contraseña y su confirmación no coinciden.",
            },
            status_code=400,
        )

    # 3. Validar política estricta de contraseñas (Altas restricciones)
    is_valid_pwd, pwd_error_msg = validate_strong_password(new_password)
    if not is_valid_pwd:
        return templates.TemplateResponse(
            "auth/change_credentials.html",
            {
                "request": request,
                "current_user": current_user,
                "brand": brand,
                "error": pwd_error_msg,
            },
            status_code=400,
        )

    # 4. Obtener admin en la BD y actualizar
    res = await db.execute(select(Admin).where(Admin.id == current_user["id"]))
    admin = res.scalar_one_or_none()
    if not admin:
        return RedirectResponse(url="/auth/admin/login", status_code=status.HTTP_303_SEE_OTHER)

    # Verificar si el nuevo username ya está en uso por otro admin
    if clean_username != admin.username:
        exists_res = await db.execute(
            select(Admin).where(Admin.username == clean_username, Admin.id != admin.id)
        )
        if exists_res.scalar_one_or_none():
            return templates.TemplateResponse(
                "auth/change_credentials.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "brand": brand,
                    "error": f"El nombre de usuario '{clean_username}' ya está en uso.",
                },
                status_code=400,
            )

    admin.username = clean_username
    admin.password_hash = hash_password(new_password)
    admin.must_change_password = False

    await db.commit()

    # Re-emitir token actualizado
    token = create_access_token(data={"sub": str(admin.id), "role": "admin"})

    response = RedirectResponse(url="/dashboard?success=credenciales_actualizadas", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 8,
        samesite="lax",
    )
    return response


# ==============================================================================
# LOGIN REGULAR PARA EMPLEADOS
# ==============================================================================

@router.get("/login", response_class=HTMLResponse)
async def employee_login_page(
    request: Request,
    brand: BrandConfig = Depends(get_active_brand),
):
    """Login general para miembros del equipo de la agencia."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "brand": brand, "error": None},
    )


@router.post("/login")
async def employee_login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Valida credenciales de empleado."""
    result = await db.execute(
        select(Employee).where(Employee.email == email.strip().lower(), Employee.is_active == True)
    )
    emp = result.scalar_one_or_none()

    if not emp or not verify_password(password, emp.password_hash):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "brand": brand, "error": "Correo o contraseña no válidos."},
            status_code=401,
        )

    token = create_access_token(data={"sub": str(emp.id), "role": "empleado"})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 8,
        samesite="lax",
    )
    return response


# ==============================================================================
# CIERRE DE SESIÓN (LOGOUT)
# ==============================================================================

@router.get("/logout")
async def logout():
    """Limpia la cookie de sesión y redirige al inicio."""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
