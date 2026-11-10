"""
Rutas de Gestión de Negocios Afiliados (Clientes de la Agencia).

Permisos:
- Administrador (Dueño): Control total (Crear, Editar, Pausar, Activar, Eliminar, Asignar empleados).
- Empleado: Acceso exclusivo a los clientes que tiene asignados bajo su responsabilidad.
"""

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
from models.employee import Employee
from models.financial import FinancialRecord
from models.report import Report
from routes.deps import get_active_brand, require_admin, require_user
from services.auth_service import generate_client_code
from services.email_service import EmailService
from templates_engine import templates

router = APIRouter(prefix="/clientes", tags=["Clientes"])


# ==============================================================================
# LISTADO DE CLIENTES (FILTRADO POR ROL)
# ==============================================================================

@router.get("", response_class=HTMLResponse)
async def list_clients(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """
    Lista los negocios afiliados.
    - Si el usuario es Dueño: ve todos los clientes (activos, pausados, inactivos).
    - Si es Empleado: solo ve aquellos clientes asignados específicamente a su usuario.
    """
    query = select(Client).options(
        selectinload(Client.assigned_employee),
        selectinload(Client.reports),
    ).order_by(Client.created_at.desc())

    if current_user["role"] != "admin":
        # Filtro de seguridad: Un empleado SOLO ve sus clientes asignados
        query = query.where(
            Client.assigned_employee_id == current_user["id"],
            Client.status != "inactivo",
        )

    result = await db.execute(query)
    clients = result.scalars().all()

    return templates.TemplateResponse(
        "clients/list.html",
        {
            "request": request,
            "clients": clients,
            "current_user": current_user,
            "brand": brand,
        },
    )


# ==============================================================================
# CREAR NEGOCIO AFILIADO
# ==============================================================================

@router.get("/crear", response_class=HTMLResponse)
async def create_client_form(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Formulario para afiliar un nuevo negocio (Solo Dueño)."""
    # Cargar lista de empleados activos para la asignación
    res_emp = await db.execute(select(Employee).where(Employee.is_active == True))
    employees = res_emp.scalars().all()

    return templates.TemplateResponse(
        "clients/form.html",
        {
            "request": request,
            "client": None,
            "employees": employees,
            "current_user": current_user,
            "brand": brand,
        },
    )


@router.post("/crear")
async def create_client_post(
    request: Request,
    business_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    monthly_fee: float = Form(0.0),
    assigned_employee_id: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo negocio afiliado y le genera su código especial de acceso al portal."""
    clean_email = email.strip().lower()
    base_user = clean_email.split("@")[0].replace(".", "_")

    client = Client(
        business_name=business_name.strip(),
        contact_name=contact_name.strip(),
        email=clean_email,
        phone=phone.strip() if phone else None,
        monthly_fee=monthly_fee,
        assigned_employee_id=assigned_employee_id if assigned_employee_id else None,
        notes=notes.strip() if notes else None,
        status="activo",
        portal_username=base_user,
        portal_code=generate_client_code(),
        portal_enabled=True,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)

    return RedirectResponse(url=f"/clientes/{client.id}?created=ok", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# DETALLE DEL CLIENTE
# ==============================================================================

@router.get("/{client_id}", response_class=HTMLResponse)
async def client_detail(
    client_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra la ficha técnica del negocio afiliado, sus reportes y balance."""
    result = await db.execute(
        select(Client)
        .options(
            selectinload(Client.assigned_employee),
            selectinload(Client.reports),
            selectinload(Client.financial_records),
        )
        .where(Client.id == client_id)
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    # Si es empleado, validar que sea su cliente asignado
    if current_user["role"] != "admin" and client.assigned_employee_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="No tienes acceso a este cliente.")

    # Asegurar que el cliente tenga código de portal si se creó en versiones previas
    if not client.portal_code:
        client.portal_code = generate_client_code()
        if not client.portal_username:
            client.portal_username = client.email.split("@")[0].lower()
        await db.commit()

    return templates.TemplateResponse(
        "clients/detail.html",
        {
            "request": request,
            "client": client,
            "current_user": current_user,
            "brand": brand,
            "sent_access": request.query_params.get("sent_access"),
            "send_msg": request.query_params.get("send_msg"),
        },
    )


# ==============================================================================
# ENVIAR / REGENERAR ACCESO AL PORTAL DEL CLIENTE
# ==============================================================================

@router.post("/{client_id}/enviar-acceso")
async def send_client_access(
    client_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Envía al cliente por correo sus credenciales para ingresar a su portal."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    if not client.portal_code:
        client.portal_code = generate_client_code()
        await db.commit()

    # Cargar configuración de integraciones
    res_email = await db.execute(select(EmailConfig).limit(1))
    email_cfg = res_email.scalar_one_or_none()

    base_url = str(request.base_url).rstrip("/")
    portal_url = f"{base_url}/portal/login"

    send_res = await EmailService.send_client_credentials(
        config=email_cfg,
        to_email=client.email,
        client_name=client.contact_name,
        portal_username=client.portal_username or client.email,
        portal_code=client.portal_code,
        portal_url=portal_url,
        agency_name=brand.agency_name,
    )

    msg = send_res.get("message", "")
    status_flag = "ok" if send_res.get("success") else "warning"

    return RedirectResponse(
        url=f"/clientes/{client_id}?sent_access={status_flag}&send_msg={msg}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{client_id}/regenerar-codigo")
async def regenerate_client_code(
    client_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Regenera un nuevo código especial de acceso para el cliente."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    client.portal_code = generate_client_code()
    await db.commit()

    return RedirectResponse(
        url=f"/clientes/{client_id}?sent_access=regenerated&send_msg=Nuevo+código+generado+exitosamente",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# ==============================================================================
# EDITAR NEGOCIO AFILIADO (SOLO ADMIN/DUEÑO)
# ==============================================================================

@router.get("/{client_id}/editar", response_class=HTMLResponse)
async def edit_client_form(
    client_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Formulario de edición de cliente (Exclusivo para el jefe)."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    res_emp = await db.execute(select(Employee).where(Employee.is_active == True))
    employees = res_emp.scalars().all()

    return templates.TemplateResponse(
        "clients/form.html",
        {
            "request": request,
            "client": client,
            "employees": employees,
            "current_user": current_user,
            "brand": brand,
        },
    )


@router.post("/{client_id}/editar")
async def edit_client_post(
    client_id: int,
    business_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    monthly_fee: float = Form(0.0),
    status: str = Form("activo"),
    assigned_employee_id: Optional[int] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza datos del negocio afiliado."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    client.business_name = business_name.strip()
    client.contact_name = contact_name.strip()
    client.email = email.strip().lower()
    client.phone = phone.strip() if phone else None
    client.monthly_fee = monthly_fee
    client.status = status
    client.assigned_employee_id = assigned_employee_id if assigned_employee_id else None
    client.notes = notes.strip() if notes else None

    await db.commit()
    # NOTA: se usa el código literal 303 para no colisionar con el parámetro `status`.
    return RedirectResponse(url=f"/clientes/{client_id}", status_code=303)


# ==============================================================================
# PAUSAR / ACTIVAR NEGOCIO AFILIADO (PERMISO DEL DUEÑO)
# ==============================================================================

@router.post("/{client_id}/toggle-status")
async def toggle_client_status(
    client_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """El dueño puede pausar o reanudar un cliente con un solo clic."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    if client.status == "activo":
        client.status = "pausado"
    else:
        client.status = "activo"

    await db.commit()
    return RedirectResponse(url="/clientes", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# ELIMINAR / DESACTIVAR NEGOCIO AFILIADO (SOLO ADMIN/DUEÑO)
# ==============================================================================

@router.post("/{client_id}/eliminar")
async def delete_client(
    client_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Marca un cliente como inactivo (soft-delete) protegiendo el historial."""
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    client.status = "inactivo"
    await db.commit()
    return RedirectResponse(url="/clientes", status_code=status.HTTP_303_SEE_OTHER)
