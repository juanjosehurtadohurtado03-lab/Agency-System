"""
Script de Datos Semilla (Seeding) para Pruebas del SaaS.

Crea automáticamente:
1. Usuario Dueño (Admin/Root) con contraseña cifrada en bcrypt.
2. Un empleado gestor de cuentas.
3. Tres negocios afiliados de ejemplo (2 activos y 1 pausado).
4. Reportes de desempeño con plantillas HTML corporativas.
5. Registros contables para alimentar el P&L y el Dashboard.

Ejecución:
python seed.py
"""

import asyncio
from datetime import date, datetime
from pathlib import Path
from database import AsyncSessionLocal, init_db
from models.admin import Admin
from models.brand import BrandConfig
from models.client import Client
from models.employee import Employee
from models.financial import FinancialRecord
from models.report import Report
from services.auth_service import generate_random_password, hash_password, generate_client_code
from services.pdf_service import PDFService
from sqlalchemy import select


async def seed():
    print("Iniciando sembrado de datos de prueba...")
    await init_db()

    generated_admin_pass = generate_random_password(12)

    # Sincronizar SIEMPRE el archivo de credenciales con la clave realmente sembrada,
    # para que la clave del archivo coincida con la de la base de datos.
    Path("instance").mkdir(parents=True, exist_ok=True)
    Path("instance/CLAVE_INICIAL_ADMIN.txt").write_text(
        f"=======================================================\n"
        f"CREDENCIALES TEMPORALES DEL DUEÑO (PRIMER INICIO)\n"
        f"=======================================================\n"
        f"URL de Acceso: http://localhost:8000/auth/admin/login\n"
        f"Usuario:        admin\n"
        f"Clave Generada: {generated_admin_pass}\n\n"
        f"Nota: Por seguridad, al iniciar sesión se te exigirá\n"
        f"cambiar obligatoriamente tu usuario y tu contraseña.\n"
        f"=======================================================\n",
        encoding="utf-8",
    )

    async with AsyncSessionLocal() as session:
        # 1. Verificar o crear admin con clave autogenerada y cambio forzoso
        res_admin = await session.execute(select(Admin).limit(1))
        admin = res_admin.scalar_one_or_none()
        if not admin:
            admin = Admin(
                username="admin",
                password_hash=hash_password(generated_admin_pass),
                email="dueno@agencia.com",
                must_change_password=True,
            )
            session.add(admin)
            print(f"✓ Dueño creado con clave generada: usuario='admin' | clave='{generated_admin_pass}'")
        else:
            admin.username = "admin"
            admin.password_hash = hash_password(generated_admin_pass)
            admin.must_change_password = True
            print(f"✓ Contraseña del Dueño restablecida: usuario='admin' | clave='{generated_admin_pass}'")

        # 2. Configuración de Marca de la Agencia
        res_brand = await session.execute(select(BrandConfig).limit(1))
        brand = res_brand.scalar_one_or_none()
        if not brand:
            brand = BrandConfig(
                agency_name="Apex Growth Marketing",
                primary_color="#1E40AF",
                secondary_color="#3B82F6",
                accent_color="#10B981",
            )
            session.add(brand)
            print("✓ Marca corporativa inicializada: 'Apex Growth Marketing'")
        else:
            brand.agency_name = "Apex Growth Marketing"

        # 3. Empleado Gestor
        res_emp = await session.execute(select(Employee).where(Employee.email == "carlos@agencia.com"))
        emp = res_emp.scalar_one_or_none()
        if not emp:
            emp = Employee(
                name="Carlos Gestor",
                email="carlos@agencia.com",
                password_hash=hash_password("Empleado123!"),
                role="gestor",
                is_active=True,
            )
            session.add(emp)
            await session.flush()
            print("✓ Empleado creado: 'carlos@agencia.com' | clave='Empleado123!'")

        # 4. Negocios Afiliados
        res_client = await session.execute(select(Client).limit(1))
        if not res_client.scalar_one_or_none():
            c1 = Client(
                business_name="Clínica Dental San Lucas",
                contact_name="Dra. Elena Vargas",
                email="elena@dentalsanlucas.com",
                phone="+58 412 5550192",
                status="activo",
                assigned_employee_id=emp.id,
                monthly_fee=450.0,
                portal_username="elena_vargas",
                portal_code=generate_client_code(),
                portal_enabled=True,
                notes="Servicio contratado: Campañas de captación de implantes y ortodoncia.",
            )
            c2 = Client(
                business_name="Restaurante La Casona Gourmet",
                contact_name="Chef Marco Rossi",
                email="marco@lacasonagourmet.com",
                phone="+58 414 9876543",
                status="activo",
                assigned_employee_id=emp.id,
                monthly_fee=600.0,
                portal_username="marco_rossi",
                portal_code=generate_client_code(),
                portal_enabled=True,
                notes="Servicio contratado: Redes sociales y generación de reservas.",
            )
            c3 = Client(
                business_name="Boutique Moda Urbana",
                contact_name="Sofía Márquez",
                email="sofia@modaurbana.com",
                phone="+58 416 3332211",
                status="pausado",
                assigned_employee_id=emp.id,
                monthly_fee=300.0,
                portal_username="sofia_marquez",
                portal_code=generate_client_code(),
                portal_enabled=True,
                notes="Cliente temporalmente en pausa por remodelación de local.",
            )
            session.add_all([c1, c2, c3])
            await session.flush()
            print("✓ 3 Clientes afiliados creados (2 activos, 1 pausado)")

            # 5. Generar reporte inicial
            rep = Report(
                client_id=c1.id,
                employee_id=emp.id,
                title="Reporte de Campañas Digitales - Octubre 2026",
                description="Resultados sobresalientes durante el período:\n- 54 Nuevas citas de valoración agendadas.\n- Retorno de inversión en pauta publicitaria (ROAS): 3.8x\n- Costo por adquisición reducido en un 22% gracias a la optimización de segmentación local.",
                period_month=10,
                period_year=2026,
                investment=500.0,
                leads=34,
                campaign_status="activa",
                status="enviado",
                sent_at=datetime.utcnow(),
            )
            session.add(rep)
            await session.flush()

            # Compilar el archivo del reporte con el branding
            doc_path = await PDFService.generate_report_document(
                report=rep,
                client=c1,
                brand=brand,
                employee_name=emp.name,
            )
            rep.file_path = doc_path
            print("✓ Reporte compilado con branding y guardado en:", doc_path)

            # 6. Registros Contables (P&L)
            fin_records = [
                FinancialRecord(type="ingreso", amount=450.0, description="Cuota mensual de marketing", client_id=c1.id, record_date=date(2026, 10, 5)),
                FinancialRecord(type="ingreso", amount=600.0, description="Cuota mensual gestión gastronómica", client_id=c2.id, record_date=date(2026, 10, 7)),
                FinancialRecord(type="gasto", amount=120.0, description="Suscripciones de software y hosting", record_date=date(2026, 10, 10)),
                FinancialRecord(type="gasto", amount=350.0, description="Honorarios del equipo de gestión", record_date=date(2026, 10, 15)),
            ]
            session.add_all(fin_records)
            print("✓ Registros de ingresos y gastos creados para el P&L")

        await session.commit()

    print("\n¡Sembrado completado con éxito!")
    print("------------------------------------------------------------------")
    print("Credenciales Temporales del Dueño (Primer Inicio):")
    print("  URL:              http://localhost:8000/auth/admin/login")
    print("  Usuario Inicial:  admin")
    print(f"  Clave Generada:   {generated_admin_pass}")
    print("  (Al ingresar se te exigirá cambiar obligatoriamente usuario y clave)")
    print("------------------------------------------------------------------")
    print("Credenciales del Empleado (Login Regular):")
    print("  URL:     http://localhost:8000/auth/login")
    print("  Correo:  carlos@agencia.com")
    print("  Clave:   Empleado123!")
    print("------------------------------------------------------------------")
    print("Credenciales de Clientes (Portal Exclusivo /portal/login):")
    print("  Clínica Dental San Lucas  -> usuario: elena_vargas")
    print("  Restaurante La Casona     -> usuario: marco_rossi")
    print("  Boutique Moda Urbana      -> usuario: sofia_marquez")
    print("  (El código especial CLI-XXXXXX se muestra en la ficha de cada cliente)")
    print("------------------------------------------------------------------")


if __name__ == "__main__":
    asyncio.run(seed())


