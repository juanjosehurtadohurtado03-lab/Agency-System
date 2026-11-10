"""
Configuración centralizada del sistema.

Utiliza Pydantic Settings para cargar variables de entorno desde el archivo .env
y proporcionar tipos estáticos validados en toda la aplicación.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """
    Clase que define todas las configuraciones del sistema SaaS.
    Si una variable no está en el archivo .env, tomará el valor por defecto aquí indicado.
    """

    # --- Seguridad y Tokens JWT ---
    SECRET_KEY: str = "super-secreto-cambiar-en-produccion-agencia-saas-2026-xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # --- Base de Datos (Ruta Absoluta Garantizada) ---
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'instance' / 'agency.db'}"

    # --- Directorios del Sistema ---
    UPLOAD_DIR: str = str(BASE_DIR / "static" / "uploads")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5 Megabytes máximo para logos

    # Configuración de carga de Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def upload_path(self) -> Path:
        """Devuelve la ruta absoluta al directorio de subidas."""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """
    Retorna la instancia singleton de las configuraciones en caché
    para evitar releer el archivo .env en cada petición HTTP.
    """
    return Settings()
