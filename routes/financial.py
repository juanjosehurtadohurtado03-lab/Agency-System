"""
Rutas de Gestión Financiera y Control de Ingresos/Gastos (P&L).

Permite al dueño:
1. Registrar entradas de dinero (pagos de clientes por servicios).
2. Registrar egresos operativos (software, publicidad, sueldos, servidores).
3. Obtener el cálculo automático del balance neto y rentabilidad.
"""

from datetime import date
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from models.brand import BrandConfig
from models.client import Client
from models.financial import FinancialRecord
from routes.deps import get_active_brand, require_admin
from templates_engine import templates

router = APIRouter(prefix="/finanzas", tags=["Finanzas"])


@router.get("", response_class=HTMLResponse)
async def list_financials(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra el libro de ingresos y egresos de la agencia."""
    # Obtener movimientos ordenados por fecha
    result = await db.execute(
        select(FinancialRecord)
        .options(selectinload(FinancialRecord.client))
        .order_by(FinancialRecord.record_date.desc(), FinancialRecord.id.desc())
    )
    records = result.scalars().all()

    # Obtener lista de clientes activos para asociar ingresos
    res_clients = await db.execute(select(Client).where(Client.status != "inactivo"))
    clients = res_clients.scalars().all()

    total_ingresos = sum(r.amount for r in records if r.type == "ingreso")
    total_gastos = sum(r.amount for r in records if r.type == "gasto")
    balance_neto = total_ingresos - total_gastos

    return templates.TemplateResponse(
        "financial/list.html",
        {
            "request": request,
            "records": records,
            "clients": clients,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "balance_neto": balance_neto,
            "current_user": current_user,
            "brand": brand,
        },
    )


@router.post("/crear")
async def create_financial_record(
    type: str = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    category: Optional[str] = Form(None),
    client_id: Optional[int] = Form(None),
    record_date: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Registra un nuevo ingreso o gasto operativo."""
    parsed_date = date.fromisoformat(record_date) if record_date else date.today()

    record = FinancialRecord(
        type=type.strip(),
        amount=abs(amount),
        description=description.strip(),
        category=category.strip() if category else None,
        client_id=client_id if client_id else None,
        record_date=parsed_date,
    )
    db.add(record)
    await db.commit()

    return RedirectResponse(url="/finanzas", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{record_id}/eliminar")
async def delete_financial_record(
    record_id: int,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Elimina una transacción del registro."""
    result = await db.execute(select(FinancialRecord).where(FinancialRecord.id == record_id))
    rec = result.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Registro no encontrado.")

    await db.delete(rec)
    await db.commit()
    return RedirectResponse(url="/finanzas", status_code=status.HTTP_303_SEE_OTHER)
