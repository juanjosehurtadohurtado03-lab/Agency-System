"""
Servicio de Autenticación, Hashing y Cifrado.

Responsabilidades:
1. Encriptar y verificar contraseñas con bcrypt (función unidireccional y resistente a ataques de fuerza bruta).
2. Generar y verificar tokens de sesión JWT (JSON Web Tokens).
3. Cifrar y descifrar credenciales sensibles (claves SMTP y SendGrid) con AES (Fernet).
"""

import base64
import hashlib
import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import bcrypt
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from config import get_settings

settings = get_settings()


# ==============================================================================
# 1. GESTIÓN DE CONTRASEÑAS (BCRYPT, POLÍTICAS Y GENERACIÓN SEGURA)
# ==============================================================================

def generate_random_password(length: int = 14) -> str:
    """
    Genera una contraseña aleatoria de alta seguridad criptográfica (secrets).
    Garantiza presencia de mayúsculas, minúsculas, números y símbolos.
    """
    upper = secrets.choice(string.ascii_uppercase)
    lower = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
    remaining = [secrets.choice(alphabet) for _ in range(max(length - 4, 6))]
    password_chars = [upper, lower, digit, special] + remaining
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def generate_client_code() -> str:
    """
    Genera un código especial de acceso para clientes afiliados (ej: CLI-84920).
    Fácil de leer y copiar para el cliente que lo recibe en su correo.
    """
    random_digits = "".join(secrets.choice(string.digits) for _ in range(6))
    return f"CLI-{random_digits}"


def validate_strong_password(password: str) -> Tuple[bool, str]:
    """
    Aplica una política de contraseñas de alta restricción:
    - Mínimo 10 caracteres
    - Al menos 1 mayúscula (A-Z)
    - Al menos 1 minúscula (a-z)
    - Al menos 1 dígito (0-9)
    - Al menos 1 carácter especial (!@#$%^&*...)
    """
    if len(password) < 10:
        return False, "La nueva contraseña debe tener al menos 10 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "Debe contener al menos una letra mayúscula (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Debe contener al menos una letra minúscula (a-z)."
    if not re.search(r"[0-9]", password):
        return False, "Debe contener al menos un número (0-9)."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?~]", password):
        return False, "Debe contener al menos un carácter especial (ej: ! @ # $ % * _ -)."
    return True, "Contraseña robusta válida."

def hash_password(password: str) -> str:
    """
    Convierte una contraseña en texto plano en un hash bcrypt seguro.
    El hash resultante incluye un 'salt' aleatorio de 12 rondas.
    Es matemáticamente imposible revertir este hash a la contraseña original.
    """
    # bcrypt trabaja con bytes, por lo que codificamos la cadena a UTF-8
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara una contraseña en texto plano con un hash almacenado en la base de datos.
    Devuelve True si coinciden, False en caso contrario.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# ==============================================================================
# 2. TOKENS DE SESIÓN (JWT - JSON WEB TOKENS)
# ==============================================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un token JWT firmado criptográficamente con la SECRET_KEY.
    Contiene claims como el ID de usuario ('sub'), su rol ('role') y la fecha de expiración ('exp').
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica y decodifica un token JWT.
    Si el token fue alterado o ya expiró, devuelve None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# ==============================================================================
# 3. CIFRADO SIMÉTRICO PARA CREDENCIALES (FERNET / AES-128)
# ==============================================================================

def _get_fernet() -> Fernet:
    """
    Deriva una clave de 32 bytes en base64 a partir de la SECRET_KEY
    para inicializar el cifrador simétrico Fernet.
    """
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    b64_key = base64.urlsafe_b64encode(key_hash)
    return Fernet(b64_key)


def encrypt_secret(secret_text: str) -> str:
    """Cifra un texto confidencial (clave SMTP / API Key) para almacenarlo seguro en SQLite."""
    if not secret_text:
        return ""
    f = _get_fernet()
    encrypted_bytes = f.encrypt(secret_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    """Descifra una clave confidencial almacenada."""
    if not encrypted_text:
        return ""
    try:
        f = _get_fernet()
        decrypted_bytes = f.decrypt(encrypted_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        return ""

