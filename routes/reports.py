"""
Rutas de Generación, Envío y Gestión de Reportes.

Permite:
1. Crear reportes periódicos para los negocios afiliados.
2. Compilar el documento corporativo con la marca de la agencia (PDF/HTML).
3. Disparar el envío automático por SMTP, SendGrid o Webhook al cliente.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.brand import BrandConfig
from models.client import Client
from models.email_config import EmailConfig
from models.report import Report
from routes.deps import get_active_brand, require_admin, require_user
from services.email_service import EmailService
from services.pdf_service import PDFService
from templates_engine import templates

router = APIRouter(prefix="/reportes", tags=["Reportes"])


# ==============================================================================
# LISTADO DE REPORTES
# ==============================================================================

@router.get("", response_class=HTMLResponse)
async def list_reports(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """
    Lista de reportes:
    - Dueño: ve los reportes de todos los clientes.
    - Empleado: solo los de sus clientes asignados.
    """
    query = select(Report).options(
        selectinload(Report.client),
        selectinload(Report.employee),
    ).order_by(Report.created_at.desc())

    if current_user["role"] != "admin":
        # Filtrar por clientes asignados al empleado
        query = query.join(Client).where(Client.assigned_employee_id == current_user["id"])

    result = await db.execute(query)
    reports = result.scalars().all()

    return templates.TemplateResponse(
        "reports/list.html",
        {
            "request": request,
            "reports": reports,
            "current_user": current_user,
            "brand": brand,
        },
    )


# ==============================================================================
# CREAR REPORTE
# ==============================================================================

@router.get("/crear", response_class=HTMLResponse)
async def create_report_form(
    request: Request,
    client_id: Optional[int] = None,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Formulario para generar un nuevo reporte mensual."""
    client_query = select(Client).where(Client.status == "activo")
    if current_user["role"] != "admin":
        client_query = client_query.where(Client.assigned_employee_id == current_user["id"])

    res_clients = await db.execute(client_query)
    clients = res_clients.scalars().all()

    now = datetime.now()
    return templates.TemplateResponse(
        "reports/form.html",
        {
            "request": request,
            "report": None,
            "clients": clients,
            "selected_client_id": client_id,
            "current_month": now.month,
            "current_year": now.year,
            "current_user": current_user,
            "brand": brand,
        },
    )


@router.post("/crear")
async def create_report_post(
    request: Request,
    client_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    period_month: int = Form(...),
    period_year: int = Form(...),
    investment: Optional[float] = Form(0.0),
    leads: Optional[int] = Form(0),
    campaign_status: Optional[str] = Form("activa"),
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Crea el reporte y compila el documento base con branding."""
    # Verificar acceso al cliente
    res_client = await db.execute(select(Client).where(Client.id == client_id))
    client = res_client.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    if current_user["role"] != "admin" and client.assigned_employee_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes permiso sobre este cliente.")

    emp_id = current_user["id"] if current_user["role"] != "admin" else client.assigned_employee_id

    report = Report(
        client_id=client_id,
        employee_id=emp_id,
        title=title.strip(),
        description=description.strip() if description else None,
        period_month=period_month,
        period_year=period_year,
        investment=investment or 0.0,
        leads=leads or 0,
        campaign_status=(campaign_status or "activa").strip().lower(),
        status="borrador",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    # Generar documento HTML/PDF con la marca de la agencia
    doc_path = await PDFService.generate_report_document(
        report=report,
        client=client,
        brand=brand,
        employee_name=current_user.get("name"),
    )
    report.file_path = doc_path
    await db.commit()

    return RedirectResponse(url=f"/reportes/{report.id}", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# DETALLE DEL REPORTE
# ==============================================================================

@router.get("/{report_id}", response_class=HTMLResponse)
async def report_detail(
    report_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Visualización previa del reporte y opciones de envío."""
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.client), selectinload(Report.employee))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")

    # Validar acceso
    if current_user["role"] != "admin" and report.client.assigned_employee_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes acceso a este reporte.")

    # Cargar estado de la integración de correo
    res_email = await db.execute(select(EmailConfig).limit(1))
    email_cfg = res_email.scalar_one_or_none()

    return templates.TemplateResponse(
        "reports/detail.html",
        {
            "request": request,
            "report": report,
            "email_config": email_cfg,
            "current_user": current_user,
            "brand": brand,
            "send_status": request.query_params.get("send_status"),
            "send_msg": request.query_params.get("send_msg"),
        },
    )


# ==============================================================================
# ENVIAR REPORTE AUTOMÁTICAMENTE (EMAIL / WEBHOOK)
# ==============================================================================

@router.post("/{report_id}/enviar")
async def send_report(
    report_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Dispara el envío del reporte al cliente afiliado vía SMTP, SendGrid o Webhook."""
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.client))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")

    # Cargar configuración de integraciones
    res_email = await db.execute(select(EmailConfig).limit(1))
    email_cfg = res_email.scalar_one_or_none()

    base_url = str(request.base_url).rstrip("/")
    report_url = f"{base_url}/{report.file_path}" if report.file_path else ""

    send_res = await EmailService.send_report_notification(
        config=email_cfg,
        to_email=report.client.email,
        client_name=report.client.contact_name,
        report_title=report.title,
        report_url=report_url,
    )

    if send_res.get("success"):
        report.status = "enviado"
        report.sent_at = datetime.utcnow()
        await db.commit()
        return RedirectResponse(
            url=f"/reportes/{report_id}?send_status=ok&send_msg=Reporte+enviado+con+éxito",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    else:
        err_msg = send_res.get("message", "Error de envío")
        return RedirectResponse(
            url=f"/reportes/{report_id}?send_status=error&send_msg={err_msg}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


# ==============================================================================
# ELIMINAR REPORTE (SOLO ADMIN)
# ==============================================================================

@router.post("/{report_id}/eliminar")
async def delete_report(
    report_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Elimina el reporte (Permiso exclusivo del dueño)."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")

    await db.delete(report)
    await db.commit()
    return RedirectResponse(url="/reportes", status_code=status.HTTP_303_SEE_OTHER)
