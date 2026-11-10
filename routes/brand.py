"""
Rutas de Personalización de Marca (White-Label) de la Agencia.

Permite al dueño:
1. Subir el logo corporativo de la agencia.
2. Definir los colores primario, secundario y de acento.
3. Personalizar el encabezado y pie de página de los reportes PDF.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from database import get_db
from models.brand import BrandConfig
from routes.deps import get_active_brand, require_admin
from templates_engine import templates

router = APIRouter(prefix="/marca", tags=["Marca"])
settings = get_settings()


def _is_valid_css_color(value: str) -> bool:
    """Valida de forma segura un color CSS (hex, rgb/rgba o nombre simple)."""
    import re
    value = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}", value):
        return True
    if re.fullmatch(r"rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*(,\s*(0|1|0?\.\d+)\s*)?\)", value):
        return True
    if re.fullmatch(r"[a-zA-Z]{3,30}", value):
        return True
    return False


@router.get("", response_class=HTMLResponse)
async def brand_settings_page(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra el panel de configuración de identidad corporativa de la agencia."""
    return templates.TemplateResponse(
        "brand/settings.html",
        {
            "request": request,
            "brand": brand,
            "current_user": current_user,
            "success": request.query_params.get("success"),
        },
    )


@router.post("")
async def update_brand_settings(
    request: Request,
    agency_name: str = Form(...),
    primary_color: str = Form("#1E40AF"),
    secondary_color: str = Form("#3B82F6"),
    accent_color: str = Form("#10B981"),
    admin_login_color: Optional[str] = Form(None),
    portal_custom_domain: Optional[str] = Form(None),
    pdf_header_html: Optional[str] = Form(None),
    pdf_footer_html: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(require_admin),
    brand: BrandConfig = Depends(get_active_brand),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza nombres, paleta de colores y plantillas HTML de los reportes."""
    brand.agency_name = agency_name.strip()
    brand.primary_color = primary_color.strip()
    brand.secondary_color = secondary_color.strip()
    brand.accent_color = accent_color.strip()

    # Color de poder del login del dueño (validar formato hex o rgb, si no, mantener)
    if admin_login_color:
        val = admin_login_color.strip()
        if _is_valid_css_color(val):
            brand.admin_login_color = val

    # Dominio propio del portal (marca blanca completa)
    brand.portal_custom_domain = (portal_custom_domain.strip() or None) if portal_custom_domain else None

    brand.pdf_header_html = pdf_header_html.strip() if pdf_header_html else None
    brand.pdf_footer_html = pdf_footer_html.strip() if pdf_footer_html else None

    await db.commit()
    return RedirectResponse(url="/marca?success=configuracion_guardada", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logo")
async def upload_agency_logo(
    logo: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(require_admin),
    brand: BrandConfig = Depends(get_active_brand),
    db: AsyncSession = Depends(get_db),
):
    """Recibe y almacena el logotipo oficial de la agencia."""
    if not logo.filename:
        return RedirectResponse(url="/marca", status_code=status.HTTP_303_SEE_OTHER)

    # Validar extensión
    ext = Path(logo.filename).suffix.lower()
    if ext not in [".png", ".jpg", ".jpeg", ".svg", ".webp"]:
        raise HTTPException(status_code=400, detail="Formato de imagen no soportado (usa PNG, JPG, WEBP o SVG).")

    logos_dir = Path("static/uploads/logos")
    logos_dir.mkdir(parents=True, exist_ok=True)

    filename = f"logo_agencia_{brand.id}{ext}"
    dest_path = logos_dir / filename

    # Guardar archivo de forma asíncrona
    contents = await logo.read()
    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(contents)

    brand.logo_path = f"static/uploads/logos/{filename}"
    await db.commit()

    return RedirectResponse(url="/marca?success=logo_actualizado", status_code=status.HTTP_303_SEE_OTHER)
