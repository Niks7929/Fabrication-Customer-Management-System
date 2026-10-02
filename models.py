from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # admin, manager, staff, customer
    description = db.Column(db.String(255), nullable=True)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='customer') # admin, manager, staff, customer
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    role_rel = db.relationship('Role', backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=False) # EMP-1001
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    department = db.Column(db.String(50), default='Production Workshop') # Workshop, On-Site Fitting, Quality Control, Design
    designation = db.Column(db.String(50), default='Fitter / Welder') # Welder, Fitter, CNC Operator, Painter, Site Supervisor
    phone = db.Column(db.String(20), nullable=False)
    hourly_rate = db.Column(db.Float, default=150.0)
    joining_date = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    user = db.relationship('User', backref=db.backref('employee_profile', uselist=False))

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    customer_code = db.Column(db.String(20), unique=True, nullable=False) # e.g., CUST-1001
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_type = db.Column(db.String(20), default='Individual') # Individual or Company
    company_name = db.Column(db.String(120), nullable=True)
    contact_person = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    gst_number = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True, default='Maharashtra')
    pincode = db.Column(db.String(10), nullable=True)
    site_addresses = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('customer_profile', uselist=False))
    enquiries = db.relationship('Enquiry', backref='customer', lazy=True)
    quotations = db.relationship('Quotation', backref='customer', lazy=True)
    jobs = db.relationship('JobOrder', backref='customer', lazy=True)
    invoices = db.relationship('Invoice', backref='customer', lazy=True)
    service_tickets = db.relationship('ServiceTicket', backref='customer', lazy=True)

class Enquiry(db.Model):
    __tablename__ = 'enquiries'
    id = db.Column(db.Integer, primary_key=True)
    enquiry_code = db.Column(db.String(20), unique=True, nullable=False) # ENQ-2001
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    project_name = db.Column(db.String(150), nullable=False)
    fabrication_type = db.Column(db.String(50), nullable=False) # MS, SS, Aluminium, Structural, Laser Cutting
    project_category = db.Column(db.String(50), default='Commercial') # Residential, Commercial, Industrial, Government
    site_location = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    budget_estimate = db.Column(db.Float, default=0.0)
    required_completion_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(30), default='Pending') # Pending, Site Visit Scheduled, Quotation Generated, Converted to Order, Rejected
    assigned_manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    site_visits = db.relationship('SiteVisit', backref='enquiry', cascade="all, delete-orphan", lazy=True)

class SiteVisit(db.Model):
    __tablename__ = 'site_visits'
    id = db.Column(db.Integer, primary_key=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiries.id'), nullable=False)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow)
    engineer_name = db.Column(db.String(100), nullable=False)
    site_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='Scheduled') # Scheduled, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    measurements = db.relationship('Measurement', backref='site_visit', cascade="all, delete-orphan", lazy=True)

class Measurement(db.Model):
    __tablename__ = 'measurements'
    id = db.Column(db.Integer, primary_key=True)
    site_visit_id = db.Column(db.Integer, db.ForeignKey('site_visits.id'), nullable=False)
    item_name = db.Column(db.String(150), nullable=False)
    length_mm = db.Column(db.Float, default=0.0)
    width_mm = db.Column(db.Float, default=0.0)
    height_mm = db.Column(db.Float, default=0.0)
    thickness_mm = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, default=1)
    notes = db.Column(db.Text, nullable=True)

class Quotation(db.Model):
    __tablename__ = 'quotations'
    id = db.Column(db.Integer, primary_key=True)
    quote_code = db.Column(db.String(20), unique=True, nullable=False) # QT-3001
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiries.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    version = db.Column(db.String(10), default='v1.0')
    valid_until = db.Column(db.Date, nullable=True)
    
    # Fabrication Parameters & Financial Breakdown
    material_cost = db.Column(db.Float, default=0.0)
    labour_cost = db.Column(db.Float, default=0.0)
    machining_cutting_cost = db.Column(db.Float, default=0.0)
    finishing_painting_cost = db.Column(db.Float, default=0.0)
    transportation_cost = db.Column(db.Float, default=0.0)
    installation_cost = db.Column(db.Float, default=0.0)
    wastage_cost = db.Column(db.Float, default=0.0)
    
    subtotal = db.Column(db.Float, default=0.0)
    gst_rate = db.Column(db.Float, default=18.0)
    gst_amount = db.Column(db.Float, default=0.0)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    estimated_margin_pct = db.Column(db.Float, default=22.5)
    
    status = db.Column(db.String(30), default='Draft') # Draft, Sent, Approved, Revised, Rejected
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('QuotationItem', backref='quotation', cascade="all, delete-orphan", lazy=True)
    enquiry = db.relationship('Enquiry', backref='quotations', lazy=True)
    revisions = db.relationship('QuotationRevision', backref='quotation', cascade="all, delete-orphan", lazy=True)

class QuotationItem(db.Model):
    __tablename__ = 'quotation_items'
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
    item_name = db.Column(db.String(150), nullable=False)
    material_type = db.Column(db.String(50), nullable=False) # MS, SS 304, SS 316, Aluminium, Brass
    material_grade = db.Column(db.String(50), nullable=True)
    thickness_mm = db.Column(db.Float, default=0.0)
    length_mm = db.Column(db.Float, default=0.0)
    width_mm = db.Column(db.Float, default=0.0)
    cutting_size = db.Column(db.String(100), nullable=True)
    weight_kg = db.Column(db.Float, default=0.0)
    quantity = db.Column(db.Integer, default=1)
    welding_details = db.Column(db.String(100), nullable=True)
    finishing_details = db.Column(db.String(100), nullable=True)
    painting_details = db.Column(db.String(100), nullable=True)
    
    total_price = db.Column(db.Float, default=0.0)

class QuotationRevision(db.Model):
    __tablename__ = 'quotation_revisions'
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=False)
    revision_number = db.Column(db.String(10), nullable=False) # v1.1, v1.2
    revised_amount = db.Column(db.Float, default=0.0)
    revised_by = db.Column(db.String(100), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    revised_at = db.Column(db.DateTime, default=datetime.utcnow)

class JobOrder(db.Model):
    __tablename__ = 'job_orders'
    id = db.Column(db.Integer, primary_key=True)
    job_code = db.Column(db.String(20), unique=True, nullable=False) # JOB-4001
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    project_name = db.Column(db.String(150), nullable=False)
    
    status = db.Column(db.String(30), default='Approved') # Approved, Production, Ready, Delivered, Installed, Completed
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High, Urgent
    
    start_date = db.Column(db.Date, nullable=True)
    target_completion_date = db.Column(db.Date, nullable=True)
    actual_completion_date = db.Column(db.Date, nullable=True)
    
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_worker_names = db.Column(db.String(255), nullable=True)
    site_address = db.Column(db.Text, nullable=True)
    drawing_notes = db.Column(db.Text, nullable=True)
    
    total_contract_value = db.Column(db.Float, default=0.0)
    advance_paid = db.Column(db.Float, default=0.0)
    balance_due = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quotation = db.relationship('Quotation', backref='job', uselist=False)
    supervisor = db.relationship('User', foreign_keys=[supervisor_id])
    stages = db.relationship('ProductionStage', backref='job', cascade="all, delete-orphan", lazy=True)
    job_cards = db.relationship('JobCard', backref='job', cascade="all, delete-orphan", lazy=True)
    labour_logs = db.relationship('JobLabourLog', backref='job', cascade="all, delete-orphan", lazy=True)
    documents = db.relationship('JobDocument', backref='job', cascade="all, delete-orphan", lazy=True)
    invoices = db.relationship('Invoice', backref='job', lazy=True)
    deliveries = db.relationship('Delivery', backref='job', cascade="all, delete-orphan", lazy=True)
    installations = db.relationship('Installation', backref='job', cascade="all, delete-orphan", lazy=True)
    quality_checks = db.relationship('QualityCheck', backref='job', cascade="all, delete-orphan", lazy=True)

class JobCard(db.Model):
    __tablename__ = 'job_cards'
    id = db.Column(db.Integer, primary_key=True)
    card_code = db.Column(db.String(20), unique=True, nullable=False) # CARD-5001
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    stage_name = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='Pending') # Pending, In Progress, Completed
    completion_pct = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    assigned_staff = db.relationship('User', foreign_keys=[assigned_staff_id])

class ProductionStage(db.Model):
    __tablename__ = 'production_stages'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    stage_name = db.Column(db.String(100), nullable=False) # Design, Cutting, Welding, Grinding, Painting, QC, Installation
    sequence_order = db.Column(db.Integer, default=1)
    status = db.Column(db.String(30), default='Pending') # Pending, In Progress, Completed
    completion_pct = db.Column(db.Integer, default=0)
    assigned_worker = db.Column(db.String(100), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

class JobLabourLog(db.Model):
    __tablename__ = 'job_labour_logs'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    worker_name = db.Column(db.String(100), nullable=False)
    work_date = db.Column(db.Date, default=datetime.utcnow)
    hours_worked = db.Column(db.Float, default=0.0)
    hourly_rate = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    stage_name = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.String(255), nullable=True)

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(20), unique=True, nullable=False) # MAT-5001
    item_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), nullable=False) # Raw Sheet, Pipe/Tube, Angle/Beam, Consumable, Fasteners, Paint
    material_type = db.Column(db.String(50), nullable=False) # MS, SS 304, SS 316, Aluminium, Hardware
    dimensions = db.Column(db.String(100), nullable=True)
    unit = db.Column(db.String(20), default='Kg') # Kg, Meter, Sheet, Piece, Litre
    unit_cost = db.Column(db.Float, default=0.0)
    quantity_in_stock = db.Column(db.Float, default=0.0)
    reorder_level = db.Column(db.Float, default=10.0)
    supplier_name = db.Column(db.String(100), nullable=True)

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    id = db.Column(db.Integer, primary_key=True)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=True)
    movement_type = db.Column(db.String(30), nullable=False) # Purchase, Issued to Job, Return, Wastage
    quantity = db.Column(db.Float, nullable=False)
    unit_cost = db.Column(db.Float, default=0.0)
    remarks = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    inventory_item = db.relationship('InventoryItem', backref='movements')

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    supplier_name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    gst_number = db.Column(db.String(30), nullable=True)
    material_supplied = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    po_code = db.Column(db.String(20), unique=True, nullable=False) # PO-6001
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.Date, default=datetime.utcnow)
    expected_delivery = db.Column(db.Date, nullable=True)
    total_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='Ordered') # Draft, Ordered, Received, Cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    supplier = db.relationship('Supplier', backref='purchase_orders')

class Delivery(db.Model):
    __tablename__ = 'deliveries'
    id = db.Column(db.Integer, primary_key=True)
    delivery_code = db.Column(db.String(20), unique=True, nullable=False) # DEL-6001
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    dispatch_date = db.Column(db.Date, default=datetime.utcnow)
    vehicle_number = db.Column(db.String(50), nullable=True)
    driver_name = db.Column(db.String(100), nullable=True)
    driver_phone = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(30), default='Dispatched') # Dispatched, In Transit, Delivered
    delivered_at = db.Column(db.DateTime, nullable=True)

class Installation(db.Model):
    __tablename__ = 'installations'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    site_supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    installation_date = db.Column(db.Date, default=datetime.utcnow)
    site_address = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='In Progress') # In Progress, Installed, Handed Over
    customer_signoff = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, nullable=True)

    supervisor = db.relationship('User', foreign_keys=[site_supervisor_id])

class QualityCheck(db.Model):
    __tablename__ = 'quality_checks'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    inspector_name = db.Column(db.String(100), nullable=False)
    weld_quality = db.Column(db.String(30), default='Passed') # Passed, Minor Defect, Failed
    dimension_check = db.Column(db.String(30), default='Passed')
    paint_finish_check = db.Column(db.String(30), default='Passed')
    overall_status = db.Column(db.String(30), default='Passed') # Passed, Conditional Pass, Rejected
    inspection_date = db.Column(db.DateTime, default=datetime.utcnow)
    remarks = db.Column(db.Text, nullable=True)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_code = db.Column(db.String(20), unique=True, nullable=False) # INV-7001
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    invoice_date = db.Column(db.Date, default=datetime.utcnow)
    due_date = db.Column(db.Date, nullable=True)
    billing_type = db.Column(db.String(30), default='Advance') # Advance, Milestone, Partial, Final
    
    subtotal = db.Column(db.Float, default=0.0)
    gst_rate = db.Column(db.Float, default=18.0)
    gst_amount = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    paid_amount = db.Column(db.Float, default=0.0)
    balance_amount = db.Column(db.Float, default=0.0)
    
    payment_status = db.Column(db.String(30), default='Unpaid') # Unpaid, Partially Paid, Paid, Overdue
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship('Payment', backref='invoice', cascade="all, delete-orphan", lazy=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    payment_code = db.Column(db.String(20), unique=True, nullable=False) # PAY-8001
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    payment_date = db.Column(db.Date, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    payment_mode = db.Column(db.String(50), default='UPI/GPay') # Cash, UPI/GPay, Bank Transfer, Cheque, Card
    reference_no = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceTicket(db.Model):
    __tablename__ = 'service_tickets'
    id = db.Column(db.Integer, primary_key=True)
    ticket_code = db.Column(db.String(20), unique=True, nullable=False) # SR-9001
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium') # Low, Medium, High
    status = db.Column(db.String(30), default='Open') # Open, In Progress, Resolved, Closed
    assigned_to = db.Column(db.String(100), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class JobDocument(db.Model):
    __tablename__ = 'job_documents'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_orders.id'), nullable=True)
    enquiry_id = db.Column(db.Integer, db.ForeignKey('enquiries.id'), nullable=True)
    service_ticket_id = db.Column(db.Integer, db.ForeignKey('service_tickets.id'), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), default='Drawing') # Drawing, CAD, Photo Before, Photo During, Photo After, Inspection Doc
    uploaded_by = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_name = db.Column(db.String(100), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='General') # Auth, Quotation, Job, Inventory, Billing
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
