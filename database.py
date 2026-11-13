"""
Configuración de la Base de Datos con SQLAlchemy 2.0 Asíncrono.

¿Por qué usamos Async con SQLite (aiosqlite)?
FastAPI es un framework asíncrono de alto rendimiento. Usar SQLAlchemy en modo
asíncrono evita que las consultas a la base de datos bloqueen el bucle de eventos (Event Loop),
permitiendo a la agencia atender múltiples peticiones de empleados y clientes concurrentemente.
"""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import get_settings

settings = get_settings()

# Asegurar que la carpeta instance exista para guardar el archivo SQLite
db_path = Path("instance")
db_path.mkdir(parents=True, exist_ok=True)

# 1. Crear el motor asíncrono (Engine)
# echo=False en producción para no saturar los logs con cada SELECT/INSERT
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # Necesario para SQLite en hilos concurrentes
)

# 2. Creador de sesiones asíncronas (Session Factory)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # No expirar objetos tras commit para poder usarlos en plantillas
    autocommit=False,
    autoflush=False,
)


# 3. Clase Base declarativa para todos los modelos ORM
class Base(DeclarativeBase):
    """
    Clase base de la cual heredarán todos los modelos de SQLAlchemy.
    Permite registrar metadatos de las tablas y construir el esquema automáticamente.
    """
    pass


# 4. Inyector de dependencia para FastAPI (Dependency Injection)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generador de sesión de base de datos para inyectar en las rutas con Depends(get_db).
    Abre la sesión al inicio de la petición y garantiza cerrarla al finalizar,
    previniendo fugas de memoria o bloqueos de base de datos.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 5. Función de inicialización de la base de datos
async def init_db() -> None:
    """
    Crea todas las tablas definidas en los modelos si aún no existen y
    aplica una migración ligera para añadir columnas nuevas a tablas existentes.
    Se ejecuta al iniciar la aplicación FastAPI y también desde seed.py.
    """
    # Importar los modelos para que SQLAlchemy registre sus tablas en Base.metadata
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migración automática: agregar columnas que falten en tablas ya existentes.
        # create_all NO agrega columnas a tablas preexistentes, por eso lo hacemos aquí.
        await conn.run_sync(_run_lightweight_migrations)


def _run_lightweight_migrations(sync_conn) -> None:
    """
    Añade columnas nuevas de forma segura (idempotente) a tablas ya existentes.
    Evita errores tipo 'no such column' cuando se actualiza el código sin
    recrear la base de datos. Solo agrega columnas; nunca borra datos.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    existing_tables = inspector.get_table_names()

    # Mapa: tabla -> {columna: definición SQL}
    migrations = {
        "brand_configs": {
            "admin_login_color": "VARCHAR(30) DEFAULT 'rgb(171, 35, 48)' NOT NULL",
            "portal_custom_domain": "VARCHAR(150)",
        },
        "reports": {
            "investment": "FLOAT DEFAULT 0.0",
            "leads": "INTEGER DEFAULT 0",
            "campaign_status": "VARCHAR(30) DEFAULT 'activa'",
        },
    }

    for table_name, columns in migrations.items():
        if table_name not in existing_tables:
            continue
        existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
        for col_name, col_def in columns.items():
            if col_name not in existing_cols:
                sync_conn.execute(
                    text(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}')
                )

