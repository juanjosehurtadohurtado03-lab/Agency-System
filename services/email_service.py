"""
Servicio de Integraciones: Envío Automático de Correos (SMTP, SendGrid) y Webhooks.

Permite enviar los reportes generados a los correos de los clientes afiliados
o disparar webhooks hacia herramientas de automatización como Zapier, Make o n8n.
"""

import smtplib
import urllib.request
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from models.email_config import EmailConfig
from services.auth_service import decrypt_secret


class EmailService:
    """Manejador unificado de envíos por correo y webhooks."""

    @classmethod
    async def send_report_notification(
        cls,
        config: Optional[EmailConfig],
        to_email: str,
        client_name: str,
        report_title: str,
        report_url: str,
    ) -> Dict[str, Any]:
        """
        Envía la notificación del reporte según el proveedor configurado (SMTP, SendGrid o Webhook).
        Devuelve un diccionario con el estado del envío: {'success': bool, 'message': str}.
        """
        if not config or not config.is_active:
            return {
                "success": False,
                "message": "La integración de envíos no está activa o configurada.",
            }

        subject = f"Nuevo Reporte Disponible: {report_title}"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
            <h2>Hola, {client_name}</h2>
            <p>Tu agencia ha publicado un nuevo reporte de desempeño:</p>
            <blockquote style="background: #f4f4f4; padding: 12px; border-left: 4px solid #1E40AF;">
                <strong>{report_title}</strong>
            </blockquote>
            <p>Puedes consultar y descargar tu reporte ingresando al enlace adjunto.</p>
            <p style="margin-top: 30px; font-size: 12px; color: #888;">
                Enviado por {config.from_name or 'Tu Agencia'} ({config.from_email or 'notificaciones@agencia.com'})
            </p>
        </div>
        """

        try:
            if config.provider == "smtp":
                return await cls._send_via_smtp(config, to_email, subject, body_html)
            elif config.provider == "sendgrid":
                return await cls._send_via_sendgrid(config, to_email, subject, body_html)
            elif config.provider == "webhook":
                return await cls._send_via_webhook(config, to_email, client_name, report_title, report_url)
            else:
                return {"success": False, "message": f"Proveedor '{config.provider}' desconocido."}
        except Exception as e:
            return {"success": False, "message": f"Error al procesar el envío: {str(e)}"}

    @classmethod
    async def send_client_credentials(
        cls,
        config: Optional[EmailConfig],
        to_email: str,
        client_name: str,
        portal_username: str,
        portal_code: str,
        portal_url: str,
        agency_name: str = "Tu Agencia Digital",
    ) -> Dict[str, Any]:
        """
        Envía al cliente afiliado sus credenciales especiales de acceso al Portal de Clientes.
        """
        if not config or not config.is_active:
            return {
                "success": False,
                "message": "La integración de envíos no está activa. Las credenciales se generaron y pueden copiarse manualmente.",
            }

        subject = f"Tus Credenciales de Acceso al Portal de {agency_name}"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; color: #1E293B; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #E2E8F0; border-radius: 12px;">
            <h2 style="color: #1E40AF; margin-top: 0;">Bienvenido a tu Portal de Cliente</h2>
            <p>Hola, <strong>{client_name}</strong>:</p>
            <p>Se ha habilitado tu acceso exclusivo para consultar tus reportes de desempeño, métricas mensuales y documentos emitidos por <strong>{agency_name}</strong>.</p>
            
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin: 24px 0;">
                <h4 style="margin: 0 0 12px 0; color: #475569; text-transform: uppercase; font-size: 11px; letter-spacing: 1px;">Tus Datos de Acceso</h4>
                <p style="margin: 6px 0; font-size: 14px;"><strong>Usuario / Correo:</strong> <code style="background: #E2E8F0; padding: 2px 6px; border-radius: 4px;">{portal_username}</code></p>
                <p style="margin: 6px 0; font-size: 14px;"><strong>Código Especial de Inicio de Sesión:</strong> <span style="font-size: 18px; font-weight: bold; color: #1E40AF; letter-spacing: 1px;">{portal_code}</span></p>
                <p style="margin: 12px 0 0 0; font-size: 14px;"><strong>Enlace de Ingreso:</strong> <a href="{portal_url}" style="color: #2563EB; font-weight: bold;">{portal_url}</a></p>
            </div>

            <p style="font-size: 13px; color: #64748B;">Por favor guarda este código en un lugar seguro para ingresar cuando desees revisar tus avances.</p>
            <p style="margin-top: 24px; font-size: 12px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 12px;">
                Enviado por {config.from_name or agency_name} &bull; Mensaje automático confidencial
            </p>
        </div>
        """

        try:
            if config.provider == "smtp":
                return await cls._send_via_smtp(config, to_email, subject, body_html)
            elif config.provider == "sendgrid":
                return await cls._send_via_sendgrid(config, to_email, subject, body_html)
            elif config.provider == "webhook":
                return await cls._send_via_webhook(config, to_email, client_name, f"Credenciales de acceso para {client_name}", portal_url)
            else:
                return {"success": False, "message": f"Proveedor '{config.provider}' desconocido."}
        except Exception as e:
            return {"success": False, "message": f"Error al despachar correo de credenciales: {str(e)}"}

    @classmethod
    async def send_ceo_welcome(
        cls,
        config: Optional[EmailConfig],
        to_email: str,
        ceo_name: str,
        username: str,
        generated_password: str,
        login_url: str,
        agency_name: str = "Tu Agencia SaaS",
    ) -> Dict[str, Any]:
        """
        Envía al CEO/Dueño de la agencia su contraseña generada y enlace de primer inicio de sesión.
        """
        if not config or not config.is_active:
            return {
                "success": False,
                "message": "Servidor de correo no conectado aún.",
            }

        subject = f"Tus Credenciales de Administrador - {agency_name}"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; color: #1E293B; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #E2E8F0; border-radius: 12px;">
            <h2 style="color: #1E40AF; margin-top: 0;">Activación de tu Sistema SaaS</h2>
            <p>Hola, <strong>{ceo_name}</strong>:</p>
            <p>Tu plataforma para <strong>{agency_name}</strong> ha sido instalada exitosamente. Aquí tienes tus credenciales maestras de primer acceso:</p>
            
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 18px; margin: 24px 0;">
                <p style="margin: 6px 0; font-size: 14px;"><strong>Usuario Inicial:</strong> <code>{username}</code></p>
                <p style="margin: 6px 0; font-size: 14px;"><strong>Contraseña Temporal Generada:</strong> <strong style="color: #DC2626;">{generated_password}</strong></p>
                <p style="margin: 12px 0 0 0; font-size: 14px;"><strong>Enlace de Ingreso del Dueño:</strong> <a href="{login_url}" style="color: #2563EB; font-weight: bold;">{login_url}</a></p>
            </div>

            <p style="font-size: 12px; color: #64748B;">Al ingresar por primera vez, el sistema te solicitará cambiar tu usuario y asignar tu contraseña permanente definitiva.</p>
        </div>
        """

        try:
            if config.provider == "smtp":
                return await cls._send_via_smtp(config, to_email, subject, body_html)
            elif config.provider == "sendgrid":
                return await cls._send_via_sendgrid(config, to_email, subject, body_html)
            else:
                return {"success": False, "message": "Proveedor no configurado para envío de bienvenida."}
        except Exception as e:
            return {"success": False, "message": f"Error al enviar correo al CEO: {str(e)}"}

    @classmethod
    async def _send_via_smtp(
        cls,
        config: EmailConfig,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> Dict[str, Any]:
        """Envía correo a través de servidor SMTP (Gmail, Outlook, Amazon SES, etc.)."""
        if not config.smtp_host or not config.smtp_username:
            return {"success": False, "message": "Host o usuario SMTP no configurado."}

        password = decrypt_secret(config.smtp_password_encrypted or "")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{config.from_name or 'Agencia'} <{config.from_email or config.smtp_username}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        try:
            if config.smtp_port == 465:
                # SSL directo
                with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=10) as server:
                    if password:
                        server.login(config.smtp_username, password)
                    server.send_message(msg)
            else:
                # STARTTLS (puerto 587 o 25)
                with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as server:
                    server.starttls()
                    if password:
                        server.login(config.smtp_username, password)
                    server.send_message(msg)

            return {"success": True, "message": f"Correo SMTP enviado exitosamente a {to_email}"}
        except Exception as err:
            return {"success": False, "message": f"Fallo al conectar al servidor SMTP: {str(err)}"}

    @classmethod
    async def _send_via_sendgrid(
        cls,
        config: EmailConfig,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> Dict[str, Any]:
        """Envía correo a través de la API REST v3 de SendGrid."""
        api_key = decrypt_secret(config.sendgrid_api_key_encrypted or "")
        if not api_key:
            return {"success": False, "message": "API Key de SendGrid no configurada o vacía."}

        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": config.from_email or "notificaciones@agencia.com", "name": config.from_name or "Agencia"},
            "subject": subject,
            "content": [{"type": "text/html", "value": html_body}],
        }

        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 202):
                    return {"success": True, "message": f"Correo SendGrid enviado a {to_email}"}
                return {"success": False, "message": f"SendGrid respondió código {response.status}"}
        except Exception as err:
            return {"success": False, "message": f"Error en petición SendGrid: {str(err)}"}

    @classmethod
    async def _send_via_webhook(
        cls,
        config: EmailConfig,
        to_email: str,
        client_name: str,
        report_title: str,
        report_url: str,
    ) -> Dict[str, Any]:
        """Dispara un webhook HTTP POST con el payload del reporte."""
        if not config.webhook_url:
            return {"success": False, "message": "URL de Webhook no configurada."}

        payload = {
            "event": "report_ready",
            "client_name": client_name,
            "client_email": to_email,
            "report_title": report_title,
            "report_url": report_url,
        }

        req = urllib.request.Request(
            config.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return {
                    "success": True,
                    "message": f"Webhook disparado exitosamente (HTTP {response.status})"
                }
        except Exception as err:
            return {"success": False, "message": f"Error al disparar webhook: {str(err)}"}

