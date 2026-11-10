"""
Servicio de Generación de Reportes y Plantillas PDF con Marca Blanca.

Permite compilar reportes mensuales con la identidad visual completa de la agencia:
- Logotipo oficial
- Paleta de colores corporativos (primario, secundario, acento)
- Encabezado y pie de página personalizados por el dueño
- Métricas de rendimiento y notas ejecutivas del analista/empleado
- Optimizado para impresión directa y descarga como documento PDF/HTML
"""

from pathlib import Path
from typing import Any, Dict, Optional

from models.brand import BrandConfig
from models.client import Client
from models.report import Report


class PDFService:
    """Servicio encargado de componer y guardar los reportes con diseño corporativo."""

    REPORTS_DIR = Path("static/uploads/reports")

    @classmethod
    def ensure_dir(cls) -> Path:
        """Crea el directorio de reportes si no existe."""
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.REPORTS_DIR

    @classmethod
    async def generate_report_document(
        cls,
        report: Report,
        client: Client,
        brand: Optional[BrandConfig] = None,
        employee_name: Optional[str] = None,
    ) -> str:
        """
        Genera el documento final del reporte con formato corporativo y CSS de alta resolución.
        Devuelve la ruta relativa del archivo generado.
        """
        cls.ensure_dir()

        # Configuración de marca por defecto si no hay una personalizada
        agency_name = brand.agency_name if brand else "Mi Agencia Digital"
        primary_color = brand.primary_color if brand else "#1E40AF"
        secondary_color = brand.secondary_color if brand else "#3B82F6"
        accent_color = brand.accent_color if brand else "#10B981"
        logo_html = (
            f'<img src="/{brand.logo_path}" alt="{agency_name}" style="max-height: 55px; max-width: 180px; object-fit: contain;">'
            if (brand and brand.logo_path)
            else f'<span style="font-size: 22px; font-weight: bold; color: {primary_color};">{agency_name}</span>'
        )

        # Reemplazar placeholders en el header y footer personalizados
        header_custom = ""
        if brand and brand.pdf_header_html:
            header_custom = brand.pdf_header_html.format(
                agency_name=agency_name,
                primary_color=primary_color,
                secondary_color=secondary_color,
            )

        footer_custom = ""
        if brand and brand.pdf_footer_html:
            footer_custom = brand.pdf_footer_html.format(
                agency_name=agency_name,
                primary_color=primary_color,
                secondary_color=secondary_color,
            )

        # Mes en texto
        meses = [
            "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        mes_nombre = meses[report.period_month] if 1 <= report.period_month <= 12 else str(report.period_month)

        filename = f"reporte_{client.id}_{report.period_year}_{report.period_month}_{report.id}.html"
        file_path = cls.REPORTS_DIR / filename

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{report.title} - {client.business_name}</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #1F2937;
            line-height: 1.5;
            background: #F9FAFB;
            margin: 0;
            padding: 24px;
        }}
        .report-card {{
            max-width: 800px;
            margin: 0 auto;
            background: #FFFFFF;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid {primary_color};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            background: {accent_color}22;
            color: {accent_color};
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .meta-box {{
            background: #F3F4F6;
            padding: 16px;
            border-radius: 8px;
            border-left: 4px solid {secondary_color};
        }}
        .meta-box h4 {{
            margin: 0 0 8px 0;
            color: #4B5563;
            font-size: 13px;
            text-transform: uppercase;
        }}
        .meta-box p {{
            margin: 4px 0;
            font-size: 14px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: {primary_color};
            border-bottom: 1px solid #E5E7EB;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 16px;
        }}
        .description-box {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            padding: 20px;
            border-radius: 8px;
            font-size: 15px;
            white-space: pre-line;
        }}
        .footer-bar {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #E5E7EB;
            font-size: 12px;
            color: #9CA3AF;
            text-align: center;
        }}
        @media print {{
            body {{
                background: #FFFFFF;
                padding: 0;
            }}
            .report-card {{
                box-shadow: none;
                padding: 0;
            }}
            .no-print {{
                display: none !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="no-print" style="max-width: 800px; margin: 0 auto 16px auto; display: flex; justify-content: flex-end; gap: 10px;">
        <button onclick="window.print()" style="background: {primary_color}; color: white; border: none; padding: 8px 18px; border-radius: 6px; cursor: pointer; font-weight: 600;">
            🖨️ Imprimir / Guardar como PDF
        </button>
    </div>

    <div class="report-card">
        <!-- Encabezado con Branding -->
        <div class="header-bar">
            <div>
                {logo_html}
            </div>
            <div style="text-align: right;">
                <span class="badge">Período: {mes_nombre} {report.period_year}</span>
                <p style="margin: 6px 0 0 0; font-size: 12px; color: #6B7280;">Generado: {report.created_at.strftime('%d/%m/%Y') if report.created_at else ''}</p>
            </div>
        </div>

        {header_custom}

        <h1 style="font-size: 24px; color: #111827; margin: 16px 0 24px 0;">{report.title}</h1>

        <!-- Información de Cliente y Responsable -->
        <div class="grid-2">
            <div class="meta-box">
                <h4>Negocio Afiliado</h4>
                <p><strong>{client.business_name}</strong></p>
                <p>Contacto: {client.contact_name}</p>
                <p>Email: {client.email}</p>
            </div>
            <div class="meta-box">
                <h4>Agencia Emisora</h4>
                <p><strong>{agency_name}</strong></p>
                <p>Gestor asignado: {employee_name or 'Equipo General'}</p>
                <p>Estado del reporte: <strong>{report.status.upper()}</strong></p>
            </div>
        </div>

        <!-- Cuerpo del Reporte -->
        <div class="section-title">Resumen Ejecutivo y Desempeño</div>
        <div class="description-box">
            {report.description or 'No se agregaron comentarios adicionales para este período.'}
        </div>

        <!-- Pie de Página Personalizado -->
        <div class="footer-bar">
            {footer_custom or f"&copy; {agency_name} &bull; Reporte confidencial para uso exclusivo de {client.business_name}"}
        </div>
    </div>
</body>
</html>
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return f"static/uploads/reports/{filename}"

