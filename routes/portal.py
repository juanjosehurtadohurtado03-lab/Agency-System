"""
Rutas del Portal de Autoservicio para Clientes Afiliados.

Permite a los clientes (negocios afiliados):
1. Iniciar sesión con su usuario y su código especial de acceso enviado por correo.
2. Consultar sus reportes mensuales con la marca y colores de la agencia.
3. Conocer a su gestor de cuenta asignado.
4. Total aislamiento de seguridad: no pueden ver datos de otros clientes ni del equipo interno.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.brand import BrandConfig
from models.client import Client
from models.report import Report
from routes.deps import get_active_brand, get_current_user_optional, require_client
from services.auth_service import create_access_token
from templates_engine import templates

router = APIRouter(prefix="/portal", tags=["Portal Clientes"])


# ==============================================================================
# LOGIN EXCLUSIVO PARA CLIENTES AFILIADOS
# ==============================================================================

@router.get("/login", response_class=HTMLResponse)
async def client_login_page(
    request: Request,
    brand: BrandConfig = Depends(get_active_brand),
):
    """Pantalla de acceso para negocios afiliados con su código especial."""
    return templates.TemplateResponse(
        "portal/login.html",
        {
            "request": request,
            "brand": brand,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/login")
async def client_login_post(
    request: Request,
    username: str = Form(...),
    portal_code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Verifica el usuario/correo y el código especial del cliente."""
    clean_user = username.strip().lower()
    clean_code = portal_code.strip()

    # Buscar cliente por email o por nombre de usuario de portal
    result = await db.execute(
        select(Client).where(
            (Client.email == clean_user) | (Client.portal_username == clean_user)
        )
    )
    client = result.scalar_one_or_none()

    if not client or not client.portal_enabled or client.status == "inactivo":
        return templates.TemplateResponse(
            "portal/login.html",
            {
                "request": request,
                "brand": brand,
                "error": "Negocio no encontrado o acceso deshabilitado.",
            },
            status_code=401,
        )

    # Si el servicio está PAUSADO, se bloquea el acceso al portal (servicio suspendido)
    if client.status == "pausado":
        return templates.TemplateResponse(
            "portal/login.html",
            {
                "request": request,
                "brand": brand,
                "error": "Tu servicio se encuentra pausado temporalmente. Contacta a tu agencia para reactivarlo.",
            },
            status_code=403,
        )

    # Validar el código especial
    if not client.portal_code or client.portal_code != clean_code:
        return templates.TemplateResponse(
            "portal/login.html",
            {
                "request": request,
                "brand": brand,
                "error": "El código de acceso especial es incorrecto. Verifica el correo recibido.",
            },
            status_code=401,
        )

    # Emitir token de sesión con rol "cliente"
    token = create_access_token(data={"sub": str(client.id), "role": "cliente"})

    response = RedirectResponse(url="/portal", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 12,  # 12 horas
        samesite="lax",
    )
    return response


# ==============================================================================
# DASHBOARD DEL PORTAL DEL CLIENTE
# ==============================================================================

@router.get("", response_class=HTMLResponse)
async def client_dashboard(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_client),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra el resumen de entregables y reportes del cliente autenticado."""
    result = await db.execute(
        select(Client)
        .options(
            selectinload(Client.assigned_employee),
            selectinload(Client.reports),
        )
        .where(Client.id == current_user["id"])
    )
    client = result.scalar_one_or_none()

    if not client:
        return RedirectResponse(url="/portal/login", status_code=status.HTTP_303_SEE_OTHER)

    # Filtrar solo reportes que hayan sido enviados o entregados (no borradores internos)
    client_reports = [r for r in client.reports if r.status in ("enviado", "entregado")]
    client_reports.sort(key=lambda x: x.created_at, reverse=True)

    return templates.TemplateResponse(
        "portal/dashboard.html",
        {
            "request": request,
            "client": client,
            "reports": client_reports,
            "current_user": current_user,
            "brand": brand,
        },
    )


# ==============================================================================
# VISUALIZACIÓN SEGURA DE REPORTE POR EL CLIENTE
# ==============================================================================

@router.get("/reportes/{report_id}", response_class=HTMLResponse)
async def client_view_report(
    report_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_client),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Permite al cliente ver su reporte en pantalla completa."""
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.client))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    # Seguridad: solo puede ver el reporte si pertenece a su id de cliente
    if not report or report.client_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")

    return templates.TemplateResponse(
        "portal/report_viewer.html",
        {
            "request": request,
            "report": report,
            "current_user": current_user,
            "brand": brand,
        },
    )


# ==============================================================================
# CIERRE DE SESIÓN DEL CLIENTE
# ==============================================================================

@router.get("/logout")
async def client_logout():
    """Limpia la sesión del cliente."""
    response = RedirectResponse(url="/portal/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

