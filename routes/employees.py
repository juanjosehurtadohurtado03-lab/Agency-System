"""
Rutas de Gestión de Empleados del Sistema SaaS.

Permite al dueño de la agencia registrar miembros de su equipo, asignarles roles,
gestionar sus contraseñas y ver qué clientes específicos tiene a su cargo cada uno.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.brand import BrandConfig
from models.employee import Employee
from routes.deps import get_active_brand, require_admin
from services.auth_service import hash_password
from templates_engine import templates

router = APIRouter(prefix="/empleados", tags=["Empleados"])


# ==============================================================================
# LISTADO DE EMPLEADOS
# ==============================================================================

@router.get("", response_class=HTMLResponse)
async def list_employees(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra el equipo de trabajo de la agencia y la cantidad de cuentas que gestiona."""
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.clients), selectinload(Employee.reports))
        .order_by(Employee.created_at.desc())
    )
    employees = result.scalars().all()

    return templates.TemplateResponse(
        "employees/list.html",
        {
            "request": request,
            "employees": employees,
            "current_user": current_user,
            "brand": brand,
        },
    )


# ==============================================================================
# CREAR EMPLEADO
# ==============================================================================

@router.get("/crear", response_class=HTMLResponse)
async def create_employee_form(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Formulario para dar de alta a un nuevo empleado."""
    return templates.TemplateResponse(
        "employees/form.html",
        {
            "request": request,
            "employee": None,
            "current_user": current_user,
            "brand": brand,
            "error": None,
        },
    )


@router.post("/crear")
async def create_employee_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("empleado"),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Registra al empleado con su contraseña encriptada."""
    # Verificar si el correo ya existe
    existing = await db.execute(
        select(Employee).where(Employee.email == email.strip().lower())
    )
    if existing.scalar_one_or_none():
        return templates.TemplateResponse(
            "employees/form.html",
            {
                "request": request,
                "employee": None,
                "current_user": current_user,
                "brand": brand,
                "error": "Ya existe un empleado registrado con ese correo.",
            },
            status_code=400,
        )

    emp = Employee(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=hash_password(password),
        role=role.strip(),
        is_active=True,
    )
    db.add(emp)
    await db.commit()
    await db.refresh(emp)

    return RedirectResponse(url="/empleados", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# DETALLE DEL EMPLEADO (CLIENTES A CARGO)
# ==============================================================================

@router.get("/{employee_id}", response_class=HTMLResponse)
async def employee_detail(
    employee_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Ficha de empleado con su listado de negocios asignados."""
    result = await db.execute(
        select(Employee)
        .options(selectinload(Employee.clients), selectinload(Employee.reports))
        .where(Employee.id == employee_id)
    )
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    return templates.TemplateResponse(
        "employees/detail.html",
        {
            "request": request,
            "employee": emp,
            "current_user": current_user,
            "brand": brand,
        },
    )


# ==============================================================================
# EDITAR EMPLEADO
# ==============================================================================

@router.get("/{employee_id}/editar", response_class=HTMLResponse)
async def edit_employee_form(
    employee_id: int,
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Formulario para editar datos y acceso del empleado."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    return templates.TemplateResponse(
        "employees/form.html",
        {
            "request": request,
            "employee": emp,
            "current_user": current_user,
            "brand": brand,
            "error": None,
        },
    )


@router.post("/{employee_id}/editar")
async def edit_employee_post(
    employee_id: int,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form("empleado"),
    password: Optional[str] = Form(None),
    is_active: bool = Form(True),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza datos y opcionalmente regenera la contraseña."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    emp.name = name.strip()
    emp.email = email.strip().lower()
    emp.role = role.strip()
    emp.is_active = is_active

    if password and len(password.strip()) >= 6:
        emp.password_hash = hash_password(password.strip())

    await db.commit()
    return RedirectResponse(url=f"/empleados/{employee_id}", status_code=status.HTTP_303_SEE_OTHER)


# ==============================================================================
# DESACTIVAR / ACTIVAR EMPLEADO
# ==============================================================================

@router.post("/{employee_id}/toggle-status")
async def toggle_employee_status(
    employee_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deshabilita el acceso de un empleado sin borrar sus datos históricos."""
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Empleado no encontrado.")

    emp.is_active = not emp.is_active
    await db.commit()
    return RedirectResponse(url="/empleados", status_code=status.HTTP_303_SEE_OTHER)
