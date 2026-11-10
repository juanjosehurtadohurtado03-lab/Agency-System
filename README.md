# 🚀 Sistema SaaS de Automatización y Reportes para Agencias

Sistema web completo desarrollado en **FastAPI** con base de datos **SQLite asíncrona (SQLAlchemy 2.0)**, diseñado para agencias de servicios y marketing que gestionan múltiples negocios afiliados, asignan personal especializado, emiten reportes con identidad corporativa de marca blanca (*White-Label*) y ofrecen a cada cliente un **portal de autoservicio** con acceso seguro.

---

## 📋 Características Principales

### 1. 🔐 Seguridad y Autenticación en Tres Niveles

El sistema está pensado para **venderlo como servicio SaaS**, por lo que cada tipo de usuario tiene su propio flujo de acceso, altamente seguro:

#### 👑 Dueño de la Agencia (Admin / Root) — Primer Arranque Seguro
Al inicializar el sistema por primera vez (o al ejecutar el `seed`), el sistema **genera automáticamente una contraseña temporal robusta** y la deja registrada en:
- La consola del servidor (bloque `[PRIMER INICIO]`).
- El archivo `instance/CLAVE_INICIAL_ADMIN.txt`.

El dueño accede en `/auth/admin/login` con el usuario inicial `admin` y esa clave generada. **Apenas ingresa**, el sistema:
1. Bloquea el acceso a todo el resto del SaaS (middleware `require_user`).
2. Lo redirige obligatoriamente a `/auth/admin/change-credentials`.
3. Le exige crear su **usuario definitivo** y una **contraseña nueva de alta seguridad** (mínimo 10 caracteres, mayúsculas, minúsculas, números y símbolos).
4. Guarda la nueva contraseña **encriptada con bcrypt (12 rondas)**. A partir de allí inicia sesión solo con sus credenciales definitivas.

> **Nota de despliegue comercial:** No compartas una clave fija. Cada instalación (o cada cliente SaaS) recibe su propia clave temporal autogenerada al primer arranque. Si la integración de correo está configurada, existe además `EmailService.send_ceo_welcome()` para enviársela por email al dueño.

#### 👤 Empleados / Gestores de Cuenta
- Acceso en `/auth/login` con su **correo** y contraseña.
- Permisos estrictamente limitados: solo ven y gestionan los clientes que tienen asignados.

#### 🏢 Clientes Afiliados — Portal de Autoservicio
Cada negocio afiliado recibe un **usuario de portal** y un **código especial de acceso** (formato `CLI-XXXXXX`) que la agencia le envía por correo desde la ficha del cliente.
- Acceso en `/portal/login` con su **usuario (o correo)** + **código especial**.
- Ve únicamente **sus propios reportes** (aislamiento total: no accede a otros clientes ni al panel interno).
- Los negocios **pausados** o **inactivos** no pueden entrar (servicio suspendido / dado de baja).

---

### 2. 🌙 Tema Oscuro Dinámico (Dark Mode)
- Interruptor de modo claro/oscuro en la barra superior con persistencia automática en `localStorage`.
- Paleta de alto contraste basada en TailwindCSS, tanto en el panel interno como en el portal del cliente.

### 3. 🗂️ Gestión de Negocios Afiliados y Empleados Asignados
- Cada cliente cuenta con un empleado responsable exclusivo.
- Un empleado no puede ver ni modificar los clientes de otros colegas.
- Estados de cliente: `Activo` (al día), `Pausado` (suspensión temporal) e `Inactivo` (*soft-delete*).
- Desde la ficha del cliente se puede **enviar o regenerar** el acceso del portal.

### 4. 🎨 Personalización de Marca Blanca (White-Label) & PDFs
- Subida del logotipo oficial de la agencia.
- Selector interactivo de colores corporativos (Primario, Secundario y Acento).
- **Color del Login del Dueño**: el acceso administrativo usa un degradado de "poder" rojo→negro (por defecto `rgb(171, 35, 48)`). El dueño puede **cambiarlo** desde *Marca y PDFs* (acepta `rgb(...)` o `#hex`).
- **Dominio propio del portal**: campo para registrar el dominio personalizado de marca blanca del portal del cliente (ej. `portal.tuagencia.com`).
- Editor de plantillas HTML de encabezado y pie de página para los reportes generados.
- Generación de reportes listos para imprimir o guardar en PDF (formato estándar A4).

### 5. 📊 Dashboard Ejecutivo y "El Porqué de la Agencia"
- Resumen de clientes al día vs. pausados y cálculo automático de cuotas recurrentes (MRR).
- Diagnóstico automatizado del estado de la agencia: rentabilidad, salud de la cartera y recomendaciones.
- Gráficos interactivos en tiempo real con **Chart.js** (reportes por mes y estatus de clientes).

### 6. ✉️ Configuración de Integraciones de Envío
- Servidor **SMTP** (Gmail, Outlook, Amazon SES, Zoho, etc.).
- API REST v3 de **SendGrid** con cifrado simétrico AES-128 (**Fernet**) para claves y contraseñas.
- **Webhooks** salientes para integración con **Zapier**, **Make** o **n8n**.
- Herramienta de prueba de envío en vivo desde el panel.
- Envío automático de: **credenciales del portal del cliente** y **notificación de reportes**.

### 7. 💰 Finanzas y P&L (Ganancias y Pérdidas)
- Control de cobros a clientes y gastos operativos (servidores, nómina, software, pauta).
- Cálculo automático de balance neto y margen de beneficio.

---

## 🧩 Jerarquía del Sistema: ¿Cómo se relacionan los usuarios?

El sistema tiene una **relación jerárquica estricta de arriba hacia abajo**. Esto es clave para entender (y explicar) el producto:

```
👑 DUEÑO (Admin/Root)   ← única cuenta raíz de la instalación
│   - Es el punto de partida: SIN dueño no existe nada más.
│   - Registra a los empleados.
│   - Registra a los clientes afiliados y los ASIGNA a un empleado.
│   - Configura marca, integraciones y finanzas.
│
├── 👤 EMPLEADOS (Gestores)
│       - Los crea el dueño.
│       - Cada uno solo ve/gestiona los clientes que el dueño le asignó.
│       - Generan reportes para sus clientes.
│
└── 🏢 CLIENTES AFILIADOS
        - Los crea el dueño (con empleado responsable opcional).
        - Cada uno recibe un código de portal y solo ve SUS reportes.
```

**Reglas de dependencia:**
- El **dueño** es la raíz. Empleados y clientes **no existen por sí solos**: los crea el dueño desde su panel.
- Un **cliente** puede existir sin empleado asignado (queda "del equipo de la agencia"), pero siempre nace desde el dueño.
- Un **empleado** solo accede a los clientes que el dueño le asignó (filtro de seguridad en `routes/clients.py`).
- El dueño **no puede eliminarse a sí mismo ni quedar sin cuenta**: el sistema autogenera la cuenta raíz en el primer arranque.

> 💡 **Sobre roles nuevos:** hoy existen tres roles fijos (`admin`, `empleado`, `cliente`). Las funciones futuras de *"Roles y equipo avanzados"* (supervisores, solo-lectura, permisos granulares) **ampliarían** esta jerarquía, pero **no cambian la raíz**: el dueño seguiría siendo la cuenta que crea a todos los demás y otorga los permisos.

---

## 💾 Persistencia de Datos: ¿Qué pasa con los usuarios al subir/desplegar?

Esta es una pregunta crucial para producción. El sistema **guarda todo en una base de datos SQLite local**:

- Archivo: **`instance/agency.db`**.
- Está **excluido de Git** por el `.gitignore` (`instance/`, `*.db`, `CLAVE_INICIAL_ADMIN.txt`).

**¿Qué significa esto al subirlo?**
- Los usuarios/clientes/empleados de prueba **NO se suben con el código** (porque la DB local no está en el repositorio). Son solo datos de tu máquina.
- Al desplegar en un servidor nuevo, la DB arranca **vacía**: en el primer arranque el sistema crea **automáticamente la cuenta del dueño** con clave temporal generada (o puedes ejecutar `seed.py` para demos).
- El dueño, una vez dentro, **registra sus empleados y clientes reales**.

**Recomendaciones según el escenario:**

| Escenario | Qué hacer con `instance/agency.db` |

| **Demo / pruebas** | Ejecutar `python seed.py` en el servidor para tener datos de ejemplo. |
| **Producción real** | **No** ejecutar `seed.py`. Dejar que el primer arranque cree al dueño y él cargue los datos reales. |
| **Migrar datos existentes** | Copiar manualmente el archivo `agency.db` al servidor (fuera de Git) o migrar a PostgreSQL. |

> ⚠️ **Importante:** No subas `instance/agency.db` ni `.env` a un repositorio público: contienen datos privados y la `SECRET_KEY`. El `.gitignore` ya los protege.

---

## 🗺️ Flujo de Acceso Resumido

| Usuario | URL de acceso | Credenciales | Pantalla inicial |

| 👑 Dueño (primer arranque) | `/auth/admin/login` | `admin` + clave autogenerada | Cambio forzoso de credenciales |
| 👑 Dueño (tras configurar) | `/auth/admin/login` | Usuario y clave propios | Dashboard |
| 👤 Empleado | `/auth/login` | Correo + contraseña | Dashboard (solo sus clientes) |
| 🏢 Cliente | `/portal/login` | Usuario + código `CLI-XXXXXX` | Portal de reportes |

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología | Propósito |

| **Backend** | FastAPI (Python 3.12) | Asíncrono, validación automática con Pydantic v2 |
| **ORM** | SQLAlchemy 2.0 (Async) + greenlet | Abstracción de datos segura contra inyecciones SQL |
| **Base de Datos** | SQLite3 vía `aiosqlite` | Motor embebido ligero en `instance/agency.db` |
| **Frontend** | Jinja2 + TailwindCSS (CDN) + Chart.js | Interfaz moderna, responsiva y sin compiladores complejos |
| **Criptografía** | bcrypt + python-jose (JWT) + Fernet | Hash irreversible de contraseñas, tokens de sesión y cifrado de claves API |
| **Sesión** | JWT en cookies HTTP-Only | Protección contra XSS y CSRF |

---

## 🚀 Cómo Iniciar el Sistema

Desde la terminal en el directorio del proyecto:

```bash
cd agency_system

# 1. Activar el entorno virtual
source venv/bin/activate

# 2. Instalar dependencias (solo la primera vez)
pip install -r requirements.txt

# 3. (Opcional) Generar datos demo de prueba
python seed.py

# 4. Iniciar el servidor de desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Abre tu navegador en: **`http://localhost:8000`**

> Si no ejecutas `seed.py`, el sistema **creará automáticamente** la cuenta del dueño con una **clave temporal generada** en el primer arranque (verás la clave en consola y en `instance/CLAVE_INICIAL_ADMIN.txt`).

---

## 🔑 Credenciales de Prueba (Sembradas con `python seed.py`)

> ⚠️ Las claves se generan/reemplazan en cada ejecución de `seed.py`. Revisa la salida de la consola para la **clave del dueño** de tu ejecución.

### 👑 Dueño de la Agencia (Admin/Root)
- **URL**: `http://localhost:8000/auth/admin/login`
- **Usuario**: `admin`
- **Contraseña**: *la clave generada mostrada al ejecutar `seed.py`*
- *Al ingresar te pedirá crear tu usuario y contraseña definitivos.*
- *Permisos*: panel completo, editar/pausar clientes, personal, finanzas, integraciones de correo y marca.

### 👤 Empleado (Gestor)
- **URL**: `http://localhost:8000/auth/login`
- **Correo**: `carlos@agencia.com`
- **Contraseña**: `Empleado123!`
- *Permisos*: ver y generar reportes únicamente para sus clientes asignados.

### 🏢 Clientes (Portal de Autoservicio)
- **URL**: `http://localhost:8000/portal/login`
- El **código especial** (`CLI-XXXXXX`) se muestra en la ficha de cada cliente dentro del panel del dueño, o puedes enviarlo por correo con el botón **"Enviar por Correo"**.
- Usuarios sembrados de ejemplo:
  - `elena_vargas` (Clínica Dental San Lucas — activo)
  - `marco_rossi` (Restaurante La Casona Gourmet — activo)
  - `sofia_marquez` (Boutique Moda Urbana — pausado, sin acceso)

---

## 📂 Estructura del Código

```text
agency_system/
├── config.py             # Configuración centralizada y rutas absolutas
├── database.py           # Conexión SQLAlchemy asíncrona a SQLite
├── main.py               # Instancia de FastAPI, eventos lifespan y montaje de rutas
├── app.py                # Proxy de ejecución
├── seed.py               # Generador de datos iniciales (admin, empleado, clientes con portal)
├── templates_engine.py   # Motor de plantillas compatible con Starlette 0.36+
├── models/               # Modelos ORM (Admin, Client, Employee, Report, BrandConfig, etc.)
├── routes/               # Controladores web y endpoints REST
│   ├── auth.py           #   Login dueño/empleado + cambio forzoso de credenciales
│   ├── portal.py         #   Portal de autoservicio de clientes (login con código)
│   ├── clients.py        #   CRUD de clientes + envío/regeneración de acceso al portal
│   ├── deps.py           #   Dependencias de sesión y control de roles/permisos
│   ├── dashboard.py
│   ├── employees.py
│   ├── reports.py
│   ├── brand.py
│   ├── financial.py
│   └── settings.py
├── schemas/              # Validadores de datos con Pydantic v2
├── services/             # Lógica de negocio (auth_service, email_service, pdf_service)
├── static/               # Logotipos subidos y reportes generados
│   └── uploads/
│       ├── logos/
│       └── reports/
├── templates/            # Plantillas HTML con TailwindCSS
│   ├── base.html
│   ├── auth/             #   setup.html, admin_login.html, change_credentials.html, login.html
│   ├── portal/           #   login.html, dashboard.html, report_viewer.html (cliente)
│   ├── dashboard/
│   ├── clients/
│   ├── employees/
│   ├── reports/
│   ├── brand/
│   ├── settings/
│   └── financial/
└── instance/
    ├── agency.db             # Base de datos SQLite
    └── CLAVE_INICIAL_ADMIN.txt  # Clave temporal del dueño (primer arranque)
```

---

## 🔒 Notas de Seguridad

- **Contraseñas**: nunca se guardan en texto plano; se almacenan como hash **bcrypt** irreversible (12 rondas).
- **Claves de API** (SMTP / SendGrid): cifradas con **Fernet (AES)** usando una clave derivada de `SECRET_KEY`.
- **Sesiones**: JWT firmado, almacenado en cookie **HTTP-Only** (inaccesible a JavaScript).
- **Aislamiento de roles**: el middleware de dependencias (`routes/deps.py`) bloquea el acceso cruzado entre clientes, empleados y dueño.
- **Primer arranque**: clave temporal autogenerada + cambio forzoso de credenciales antes de poder usar el sistema.
- **Portal del cliente**: exige usuario + código especial; los clientes pausados/inactivos quedan bloqueados.
- **Producción**: cambia `SECRET_KEY` en el archivo `.env`, usa HTTPS y una base de datos más robusta (PostgreSQL) si el volumen crece.

<p align="center">Hecho con ❤️ para agencias que quieren escalar su operación de forma profesional y segura.</p>

