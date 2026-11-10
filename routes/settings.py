"""
Rutas de Configuración de Integraciones de Envíos.

Permite al dueño:
1. Conectar servidores SMTP (Gmail, Zoho, Amazon SES, etc.).
2. Configurar la API Key de SendGrid.
3. Configurar Webhooks para automatizaciones con Zapier, Make o n8n.
4. Realizar pruebas de conexión en tiempo real.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.brand import BrandConfig
from models.email_config import EmailConfig
from routes.deps import get_active_brand, require_admin
from services.auth_service import decrypt_secret, encrypt_secret
from services.email_service import EmailService
from templates_engine import templates

router = APIRouter(prefix="/configuracion", tags=["Configuración"])


@router.get("/email", response_class=HTMLResponse)
async def email_settings_page(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    brand: BrandConfig = Depends(get_active_brand),
):
    """Muestra el formulario de credenciales de envío."""
    result = await db.execute(select(EmailConfig).limit(1))
    email_cfg = result.scalar_one_or_none()

    if not email_cfg:
        email_cfg = EmailConfig(provider="smtp", smtp_port=587, is_active=False)
        db.add(email_cfg)
        await db.commit()
        await db.refresh(email_cfg)

    # Descifrar contraseñas para previsualización segura enmascarada
    has_smtp_password = bool(email_cfg.smtp_password_encrypted)
    has_sendgrid_key = bool(email_cfg.sendgrid_api_key_encrypted)

    return templates.TemplateResponse(
        "settings/email.html",
        {
            "request": request,
            "config": email_cfg,
            "has_smtp_password": has_smtp_password,
            "has_sendgrid_key": has_sendgrid_key,
            "current_user": current_user,
            "brand": brand,
            "success": request.query_params.get("success"),
            "test_result": request.query_params.get("test_result"),
        },
    )


@router.post("/email")
async def update_email_settings(
    provider: str = Form("smtp"),
    smtp_host: Optional[str] = Form(None),
    smtp_port: int = Form(587),
    smtp_username: Optional[str] = Form(None),
    smtp_password: Optional[str] = Form(None),
    sendgrid_api_key: Optional[str] = Form(None),
    webhook_url: Optional[str] = Form(None),
    from_email: Optional[str] = Form(None),
    from_name: Optional[str] = Form(None),
    is_active: bool = Form(False),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Guarda las integraciones cifrando las credenciales confidenciales."""
    result = await db.execute(select(EmailConfig).limit(1))
    email_cfg = result.scalar_one_or_none()
    if not email_cfg:
        email_cfg = EmailConfig()
        db.add(email_cfg)

    email_cfg.provider = provider
    email_cfg.smtp_host = smtp_host.strip() if smtp_host else None
    email_cfg.smtp_port = smtp_port
    email_cfg.smtp_username = smtp_username.strip() if smtp_username else None
    email_cfg.webhook_url = webhook_url.strip() if webhook_url else None
    email_cfg.from_email = from_email.strip() if from_email else None
    email_cfg.from_name = from_name.strip() if from_name else None
    email_cfg.is_active = is_active

    # Cifrar credenciales solo si se enviaron valores nuevos
    if smtp_password and smtp_password.strip():
        email_cfg.smtp_password_encrypted = encrypt_secret(smtp_password.strip())

    if sendgrid_api_key and sendgrid_api_key.strip():
        email_cfg.sendgrid_api_key_encrypted = encrypt_secret(sendgrid_api_key.strip())

    await db.commit()
    return RedirectResponse(
        url="/configuracion/email?success=guardado",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/email/test")
async def test_email_connection(
    test_target_email: str = Form(...),
    current_user: Dict[str, Any] = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Envía un mensaje de prueba al correo especificado."""
    result = await db.execute(select(EmailConfig).limit(1))
    email_cfg = result.scalar_one_or_none()

    if not email_cfg:
        return RedirectResponse(
            url="/configuracion/email?test_result=error_sin_configuracion",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    res = await EmailService.send_report_notification(
        config=email_cfg,
        to_email=test_target_email.strip(),
        client_name="Prueba de Sistema",
        report_title="Test de Conexión de la Agencia",
        report_url="#",
    )

    msg = "ok" if res.get("success") else "error_" + res.get("message", "fallo")
    return RedirectResponse(
        url=f"/configuracion/email?test_result={msg}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
