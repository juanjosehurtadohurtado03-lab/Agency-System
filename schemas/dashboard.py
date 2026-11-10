"""
Esquemas del panel de control (dashboard) para el sistema de agencia SaaS.

Define los modelos Pydantic para las estadísticas y métricas
que se muestran en el dashboard principal del administrador.
Estos modelos son de solo lectura y se calculan a partir de
datos agregados del sistema.
"""

from pydantic import BaseModel, Field


# === Estadísticas generales del dashboard ===
# Modelo principal que agrupa todas las métricas clave de la agencia
class DashboardStats(BaseModel):
    """
    Modelo con las estadísticas generales del panel de control.
    
    Incluye métricas de clientes, empleados, reportes y finanzas
    para dar una visión global del estado de la agencia.
    """

    # --- Métricas de clientes ---
    total_clients: int = Field(
        ...,
        description="Número total de clientes registrados en el sistema",
        examples=[45]
    )
    active_clients: int = Field(
        ...,
        description="Número de clientes con estado 'activo'",
        examples=[38]
    )
    paused_clients: int = Field(
        ...,
        description="Número de clientes con estado 'pausado'",
        examples=[5]
    )

    # --- Métricas de empleados ---
    total_employees: int = Field(
        ...,
        description="Número total de empleados registrados",
        examples=[12]
    )

    # --- Métricas de reportes ---
    reports_this_month: int = Field(
        ...,
        description="Cantidad de reportes creados en el mes actual",
        examples=[30]
    )
    reports_sent: int = Field(
        ...,
        description="Cantidad de reportes con estado 'enviado' o 'entregado' este mes",
        examples=[25]
    )

    # --- Métricas financieras ---
    total_revenue: float = Field(
        ...,
        description="Ingresos totales acumulados",
        examples=[150000.00]
    )
    total_expenses: float = Field(
        ...,
        description="Gastos totales acumulados",
        examples=[85000.00]
    )
    profit: float = Field(
        ...,
        description="Ganancia neta (ingresos - gastos)",
        examples=[65000.00]
    )


# === Conteo mensual de reportes ===
# Se usa para gráficos de tendencia de reportes por mes
class MonthlyReportCount(BaseModel):
    """Modelo para representar el conteo de reportes en un mes específico."""

    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Mes del conteo (1-12)",
        examples=[11]
    )
    year: int = Field(
        ...,
        ge=2020,
        description="Año del conteo",
        examples=[2024]
    )
    count: int = Field(
        ...,
        ge=0,
        description="Cantidad de reportes en ese mes",
        examples=[15]
    )


# === Resumen de clientes por estado ===
# Se usa para gráficos de distribución de estados de clientes
class ClientStatusSummary(BaseModel):
    """Modelo para representar el conteo de clientes agrupados por estado."""

    status: str = Field(
        ...,
        description="Estado del grupo de clientes (activo, pausado, inactivo)",
        examples=["activo"]
    )
    count: int = Field(
        ...,
        ge=0,
        description="Cantidad de clientes con este estado",
        examples=[38]
    )
