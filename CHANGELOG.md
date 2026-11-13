# Changelog — AgencyOrder

Todos los cambios notables de este producto se documentan en este archivo.

El formato sigue el estándar [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el proyecto adopta el [Versionado Semántico](https://semver.org/lang/es/) (`MAJOR.MINOR.PATCH`):

- **MAJOR**: cambios incompatibles con versiones anteriores.
- **MINOR**: nuevas funcionalidades compatibles.
- **PATCH**: correcciones compatibles.

---

## [Sin publicar]

Aquí se registran los cambios en desarrollo que aún no forman parte de una versión estable.

---

## [1.0.0] — 2026

Primera versión funcional (MVP) de **AgencyOrder**, lista para operar una agencia
con clientes, equipo, reportes y portal de autoservicio.

### Añadido

- **Autenticación en tres niveles** con sesiones JWT en cookies HTTP-Only:
  - Dueño (Admin/Root) con primer arranque seguro + cambio forzoso de credenciales.
  - Empleados/Gestores con acceso limitado a sus clientes asignados.
  - Clientes con login por usuario + código especial (`CLI-XXXXXX`).
- **Sesiones aisladas por rol**: el panel interno (`access_token`) y el portal del
  cliente (`portal_token`) usan cookies separadas, evitando que iniciar sesión como
  cliente cierre o secuestre la sesión del panel en otra pestaña.
- **Gestión de clientes afiliados**: ficha completa (contacto, correo, teléfono,
  cuota mensual, gestor asignado, notas) y estados Activo / Pausado / Inactivo.
- **Checklist operativo de tareas** por cliente: añadir, marcar/desmarcar y eliminar
  tareas, con contador de completadas / totales.
- **Reportes con campos estructurados**: inversión, leads/resultados y estado de
  campaña (Activa / En Optimización / Pausada / Finalizada), con **costo por lead**
  calculado automáticamente.
- **Generación de PDF real** en el backend con **WeasyPrint** (HTML → PDF A4) con
  marca blanca de la agencia; *fallback* a HTML imprimible si WeasyPrint no está disponible.
- **Portal del cliente** (marca blanca): visualización de reportes, métricas y
  descarga del PDF, con aislamiento total entre clientes.
- **Integraciones de envío**: SMTP, SendGrid (API v3) y Webhooks salientes para
  enviar reportes y credenciales, con claves cifradas mediante Fernet (AES).
- **Marca y PDFs (White-Label)**: logo, colores corporativos, color del login del
  dueño, dominio propio del portal y plantillas HTML de encabezado/pie de los reportes.
- **Dashboard ejecutivo**: clientes al día vs. pausados, MRR, reportes por mes,
  gráficos con Chart.js y diagnóstico automático de la cartera.
- **Finanzas / P&L**: cobros a clientes, gastos operativos, balance neto y margen.
- **Tema claro/oscuro** con persistencia en `localStorage` en panel y portal.
- **Migraciones automáticas** de base de datos al arrancar (agrega columnas nuevas
  sin borrar datos existentes).
- **Metadatos del producto**: nombre "AgencyOrder", versión, autor, contacto y aviso
  de copyright, independientes de la marca configurable de la agencia.

### Corregido

- El inicio de sesión del cliente en una pestaña nueva ya no redirige ni interfiere
  con la sesión del dueño/empleado en el panel (cookies de sesión separadas).
- Texto invisibles en el **tema claro del portal del cliente** (se restauró el fondo
  degradado de la tarjeta de bienvenida para garantizar legibilidad del texto blanco).

### Seguridad

- Contraseñas con hash **bcrypt** (12 rondas); no se almacenan en texto plano.
- Claves de API (SMTP/SendGrid) cifradas con **Fernet** derivado de `SECRET_KEY`.
- Aislamiento de roles en el middleware de dependencias (sin accesos cruzados).
- Primer arranque con clave temporal autogenerada y cambio forzoso de credenciales.

---

## Guía rápida para mantener este archivo

Al publicar una nueva versión:

1. Mueve los cambios de **[Sin publicar]** a una nueva sección `## [X.Y.Z] — AAAA-MM-DD`.
2. Usa las categorías: **Añadido**, **Cambiado**, **Obsoleto**, **Eliminado**,
   **Corregido** y **Seguridad**.
3. Incrementa la versión según corresponda (MAJOR / MINOR / PATCH).

<!-- Enlaces de comparación de versiones (se actualizan al publicar cada versión) -->
[Sin publicar]: https://github.com/USUARIO/AgencyOrder/commits/main
[1.0.0]: https://github.com/USUARIO/AgencyOrder/releases/tag/v1.0.0
