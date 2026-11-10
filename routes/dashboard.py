"""
Rutas del Dashboard Principal y Métricas de la Agencia.

Permite al dueño:
1. Ver el estado general de la agencia en tiempo real.
2. Supervisar cuántos reportes se enviaron mes a mes.
3. Monitorear clientes al día (activos vs pausados).
4. Analizar Ganancias y Pérdidas (P&L) con desglose y explicación ejecutiva.
"""

from datetime import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.brand import BrandConfig
from models.client import Client
from models.employee import Employee
from models.financial import FinancialRecord
from models.report import Report
from routes.deps import get_active_brand, require_user
from templates_engine import templates

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_class=HTMLResponse)
async def dashboard_view(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Renderiza el panel de control con métricas ejecutivas."""
    now = datetime.now()

    # 1. Métricas de Clientes
    res_clients = await db.execute(select(Client))
    all_clients = res_clients.scalars().all()

    total_clients = len(all_clients)
    active_clients = sum(1 for c in all_clients if c.status == "activo")
    paused_clients = sum(1 for c in all_clients if c.status == "pausado")

    # Ingresos recurrentes mensuales esperados (MRR)
    mrr = sum(c.monthly_fee for c in all_clients if c.status == "activo")

    # 2. Métricas de Empleados
    res_emp = await db.execute(select(func.count(Employee.id)))
    total_employees = res_emp.scalar() or 0

    # 3. Métricas de Reportes
    res_rep = await db.execute(select(Report))
    all_reports = res_rep.scalars().all()

    total_reports = len(all_reports)
    reports_sent = sum(1 for r in all_reports if r.status in ("enviado", "entregado"))
    reports_this_month = sum(
        1 for r in all_reports if r.period_month == now.month and r.period_year == now.year
    )

    # 4. Métricas Financieras (P&L)
    res_fin = await db.execute(select(FinancialRecord))
    financial_records = res_fin.scalars().all()

    total_ingresos = sum(r.amount for r in financial_records if r.type == "ingreso")
    total_gastos = sum(r.amount for r in financial_records if r.type == "gasto")
    balance_neto = total_ingresos - total_gastos

    # 5. Generar diagnóstico ejecutivo del estado de la agencia
    porcentaje_al_dia = (active_clients / total_clients * 100) if total_clients > 0 else 0
    margen_ganancia = (balance_neto / total_ingresos * 100) if total_ingresos > 0 else 0

    if balance_neto > 0:
        diagnostico = (
            f"La agencia opera con saldo favorable (${balance_neto:,.2f}) y un margen de rentabilidad del "
            f"{margen_ganancia:.1f}%. El {porcentaje_al_dia:.0f}% de los negocios afiliados se encuentra activo "
            f"y al día, generando un MRR recurrente proyectado de ${mrr:,.2f}."
        )
    elif total_ingresos == 0 and total_gastos == 0:
        diagnostico = "Aún no se han registrado movimientos contables para el período actual."
    else:
        diagnostico = (
            f"Atención: Los gastos acumulados (${total_gastos:,.2f}) superan los ingresos "
            f"(${total_ingresos:,.2f}), generando un déficit temporal de ${abs(balance_neto):,.2f}. "
            "Se recomienda activar los clientes en pausa o revisar los costos operativos."
        )

    # 6. Últimos reportes generados
    recent_reports = sorted(all_reports, key=lambda x: x.created_at, reverse=True)[:5]

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "current_user": current_user,
            "brand": brand,
            "stats": {
                "total_clients": total_clients,
                "active_clients": active_clients,
                "paused_clients": paused_clients,
                "total_employees": total_employees,
                "total_reports": total_reports,
                "reports_sent": reports_sent,
                "reports_this_month": reports_this_month,
                "mrr": mrr,
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "balance_neto": balance_neto,
                "porcentaje_al_dia": round(porcentaje_al_dia, 1),
                "diagnostico": diagnostico,
            },
            "recent_reports": recent_reports,
        },
    )


@router.get("/api/chart-data", response_class=JSONResponse)
async def dashboard_chart_data(
    current_user: Dict[str, Any] = Depends(require_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint JSON para graficar reportes mensuales y estado de clientes con Chart.js."""
    # Contar reportes por mes
    res_rep = await db.execute(select(Report))
    reports = res_rep.scalars().all()

    # Agrupar últimos meses
    now = datetime.now()
    meses_etiquetas = []
    conteo_reportes = []

    meses_nombres = ["", "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    for i in range(5, -1, -1):
        m = (now.month - i - 1) % 12 + 1
        y = now.year if now.month - i > 0 else now.year - 1
        etiqueta = f"{meses_nombres[m]} {y}"
        meses_etiquetas.append(etiqueta)

        cant = sum(1 for r in reports if r.period_month == m and r.period_year == y)
        conteo_reportes.append(cant)

    # Estado de clientes
    res_clients = await db.execute(select(Client))
    clients = res_clients.scalars().all()
    activos = sum(1 for c in clients if c.status == "activo")
    pausados = sum(1 for c in clients if c.status == "pausado")
    inactivos = sum(1 for c in clients if c.status == "inactivo")

    return {
        "monthly_reports": {
            "labels": meses_etiquetas,
            "data": conteo_reportes,
        },
        "client_status": {
            "labels": ["Al Día (Activos)", "Pausados", "Inactivos"],
            "data": [activos, pausados, inactivos],
        },
    }
