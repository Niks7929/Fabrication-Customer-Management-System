import pymysql
from datetime import datetime, date, timedelta
from config import Config
from models import (
    db, Role, User, Employee, Customer, Enquiry, SiteVisit, Measurement,
    Quotation, QuotationItem, QuotationRevision, JobOrder, JobCard, ProductionStage,
    JobLabourLog, InventoryItem, StockMovement, Supplier, PurchaseOrder, Delivery,
    Installation, QualityCheck, Invoice, Payment, ServiceTicket, AuditLog
)

def init_db(app):
    """
    Ensures MySQL database 'fabrication_management' exists on WAMP Server
    and initializes tables and seed data.
    """
    try:
        connection = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        connection.commit()
        cursor.close()
        connection.close()
        print(f"[OK] MySQL Database '{Config.MYSQL_DB}' checked/created successfully!")
    except Exception as e:
        print(f"[WARN] Error ensuring MySQL database exists: {e}")

    with app.app_context():
        db.create_all()
        seed_sample_data()

def seed_sample_data():
    if Role.query.filter_by(name='admin').first():
        return # Database already initialized

    print("[INFO] Initializing system data & RBAC roles...")

    # 1. System Roles (Exactly 4 Roles)
    role_admin = Role(name='admin', description='Master System Control, User Security, Quotas & Full Analytics')
    role_manager = Role(name='manager', description='Project Manager: Enquiries, Quotes, Work Orders & Operations')
    role_staff = Role(name='staff', description='Production Staff: Assigned Job Cards, Stages & Daily Labour Logs')
    role_customer = Role(name='customer', description='Customer Portal: Enquiries, Quotation Approval & Order Tracking')

    db.session.add_all([role_admin, role_manager, role_staff, role_customer])
    db.session.commit()

    # 2. Master System Admin Account (Max 1 Admin)
    admin_user = User(
        username='admin',
        email='admin@apexsteel.com',
        full_name='Master Admin',
        phone='+91 98765 43210',
        role='admin',
        role_id=role_admin.id,
        is_active=True
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)
    db.session.commit()

    # 3. Raw Material & Consumable Inventory Items
    inv1 = InventoryItem(
        item_code='MAT-5001',
        item_name='Mild Steel (MS) Plate 6mm',
        category='Raw Sheet',
        material_type='MS',
        dimensions='2500mm x 1250mm x 6mm',
        unit='Sheet',
        unit_cost=4800.0,
        quantity_in_stock=45.0,
        reorder_level=10.0,
        supplier_name='Tata Steel Distributors'
    )

    inv2 = InventoryItem(
        item_code='MAT-5002',
        item_name='Stainless Steel (SS 304) Pipe 2 inch',
        category='Pipe/Tube',
        material_type='SS 304',
        dimensions='6 Meter Length, 2" OD, 2mm wall',
        unit='Meter',
        unit_cost=650.0,
        quantity_in_stock=120.0,
        reorder_level=25.0,
        supplier_name='Jindal Stainless Ltd'
    )

    inv3 = InventoryItem(
        item_code='MAT-5003',
        item_name='Aluminium Section Heavy Architectural',
        category='Angle/Beam',
        material_type='Aluminium',
        dimensions='100mm x 50mm Channel',
        unit='Kg',
        unit_cost=240.0,
        quantity_in_stock=300.0,
        reorder_level=50.0,
        supplier_name='Hindalco Extrusions'
    )
    db.session.add_all([inv1, inv2, inv3])
    db.session.commit()

    # 4. Initial Audit Log
    log1 = AuditLog(
        user_id=admin_user.id,
        user_name='Master Admin',
        action='System Initialized',
        category='Auth',
        details='WAMP Database fabrication_management seeded with RBAC roles and Master Admin.'
    )
    db.session.add(log1)
    db.session.commit()

    print("[SUCCESS] Fabrication System database initialized successfully!")
