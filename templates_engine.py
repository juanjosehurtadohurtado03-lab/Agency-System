"""
Motor de Plantillas Jinja2 Seguro y Universal.

Garantiza compatibilidad absoluta entre versiones modernas de Starlette/FastAPI
(donde el orden de argumentos de TemplateResponse cambió a request, name, context)
y asegura la resolución absoluta de la carpeta templates/.
"""

from pathlib import Path
from fastapi.templating import Jinja2Templates
from config import (
    BASE_DIR,
    PRODUCT_NAME,
    PRODUCT_VERSION,
    DEVELOPER_NAME,
    DEVELOPER_PHONE,
    COPYRIGHT_NOTICE,
    PRODUCT_FOOTER,
)


class SafeJinja2Templates(Jinja2Templates):
    """
    Subclase que intercepta llamadas en formato clásico:
        templates.TemplateResponse("ruta.html", {"request": request, ...})
    y las traduce al formato exigido por Starlette 0.36+:
        super().TemplateResponse(request=request, name="ruta.html", context={...})
    """

    def TemplateResponse(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            name = args[0]
            context = args[1] if len(args) > 1 else kwargs.get("context", {})
            request = context.get("request") if isinstance(context, dict) else kwargs.get("request")
            status_code = kwargs.get("status_code", args[2] if len(args) > 2 else 200)
            return super().TemplateResponse(
                request=request,
                name=name,
                context=context,
                status_code=status_code,
            )
        return super().TemplateResponse(*args, **kwargs)


# Instancia singleton configurada con ruta absoluta a templates
templates = SafeJinja2Templates(directory=str(BASE_DIR / "templates"))

# Metadatos del producto disponibles globalmente en todas las plantillas.
# Se acceden como {{ product_name }}, {{ copyright_notice }}, etc.
templates.env.globals.update(
    product_name=PRODUCT_NAME,
    product_version=PRODUCT_VERSION,
    developer_name=DEVELOPER_NAME,
    developer_phone=DEVELOPER_PHONE,
    copyright_notice=COPYRIGHT_NOTICE,
    product_footer=PRODUCT_FOOTER,
)

