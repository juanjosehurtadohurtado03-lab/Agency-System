"""
Punto de Entrada Principal del SaaS de Automatización de Reportes para Agencias.

Arquitectura:
- Framework: FastAPI (Asíncrono de alto rendimiento)
- ORM: SQLAlchemy 2.0 Async (aiosqlite)
- Motor de Plantillas: Jinja2 + TailwindCSS
- Autenticación: bcrypt + JWT en Cookies HTTP-Only
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from database import AsyncSessionLocal, init_db
from models.admin import Admin
from models.brand import BrandConfig
from models.email_config import EmailConfig
from routes import (
    auth_router,
    brand_router,
    clients_router,
    dashboard_router,
    employees_router,
    financial_router,
    portal_router,
    reports_router,
    settings_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida de la aplicación.
    Se ejecuta al iniciar el servidor para crear tablas y verificar registros iniciales.
    """
    # 1. Asegurar directorios físicos
    Path("instance").mkdir(parents=True, exist_ok=True)
    Path("static/uploads/logos").mkdir(parents=True, exist_ok=True)
    Path("static/uploads/reports").mkdir(parents=True, exist_ok=True)

    # 2. Inicializar tablas en SQLite
    await init_db()

    # 3. Inicializar configuración de marca y credenciales iniciales de admin
    async with AsyncSessionLocal() as session:
        # Verificar o crear cuenta de administrador inicial con clave autogenerada
        res_admin = await session.execute(select(Admin).limit(1))
        if not res_admin.scalar_one_or_none():
            from services.auth_service import generate_random_password, hash_password
            generated_pwd = generate_random_password(12)
            admin = Admin(
                username="admin",
                password_hash=hash_password(generated_pwd),
                email="admin@agencia.com",
                must_change_password=True,
            )
            session.add(admin)
            await session.flush()

            # Guardar copia de respaldo en instance/CLAVE_INICIAL_ADMIN.txt
            cred_path = Path("instance/CLAVE_INICIAL_ADMIN.txt")
            cred_path.write_text(
                f"=======================================================\n"
                f"CREDENCIALES TEMPORALES DEL DUEÑO (PRIMER INICIO)\n"
                f"=======================================================\n"
                f"URL de Acceso: http://localhost:8000/auth/admin/login\n"
                f"Usuario:        admin\n"
                f"Clave Generada: {generated_pwd}\n\n"
                f"Nota: Por seguridad, al iniciar sesión se te exigirá\n"
                f"cambiar obligatoriamente tu usuario y tu contraseña.\n"
                f"=======================================================\n",
                encoding="utf-8",
            )
            print("\n" + "=" * 65)
            print("🔑 [PRIMER INICIO] CUENTA DEL DUEÑO CREADA CON CLAVE GENERADA:")
            print("   URL de Login:    http://localhost:8000/auth/admin/login")
            print("   Usuario Inicial: admin")
            print(f"   Clave Temporal:  {generated_pwd}")
            print("   (Guarda este dato; al entrar deberás cambiar tu usuario y clave)")
            print("=" * 65 + "\n")

        res_brand = await session.execute(select(BrandConfig).limit(1))
        if not res_brand.scalar_one_or_none():
            brand = BrandConfig(
                agency_name="Mi Agencia Digital",
                primary_color="#1E40AF",
                secondary_color="#3B82F6",
                accent_color="#10B981",
            )
            session.add(brand)

        res_email = await session.execute(select(EmailConfig).limit(1))
        if not res_email.scalar_one_or_none():
            email_cfg = EmailConfig(provider="smtp", smtp_port=587, is_active=False)
            session.add(email_cfg)

        await session.commit()

    yield  # La aplicación atiende peticiones aquí


# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="SaaS Automatización de Reportes para Agencias",
    description="Sistema multi-rol para gestión de clientes afiliados, métricas y reportes automáticos con marca blanca.",
    version="1.0.0",
    lifespan=lifespan,
)

# Servir archivos estáticos (logos, CSS, reportes generados)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusión de enrutadores modulares
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(clients_router)
app.include_router(employees_router)
app.include_router(reports_router)
app.include_router(brand_router)
app.include_router(settings_router)
app.include_router(financial_router)
app.include_router(portal_router)


@app.get("/")
async def root():
    """Redirige la raíz al dashboard o a la pantalla correspondiente según el estado de la sesión."""
    return RedirectResponse(url="/dashboard", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

