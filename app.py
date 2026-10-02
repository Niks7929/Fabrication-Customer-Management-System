import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models import (
    db, Role, User, Employee, Customer, Enquiry, SiteVisit, Measurement,
    Quotation, QuotationItem, QuotationRevision, JobOrder, JobCard, ProductionStage,
    JobLabourLog, InventoryItem, StockMovement, Supplier, PurchaseOrder, Delivery,
    Installation, QualityCheck, Invoice, Payment, ServiceTicket, JobDocument, AuditLog
)
from database import init_db
from helpers import admin_required, staff_required, save_uploaded_file, generate_next_code

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Custom jinja uppercase filter
@app.template_filter('uppercase')
def uppercase_filter(s):
    return s.upper() if s else ''

def log_audit(action, category='General', details=None):
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        user_name = current_user.full_name if current_user.is_authenticated else 'Anonymous'
        log = AuditLog(
            user_id=user_id,
            user_name=user_name,
            action=action,
            category=category,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass

# Initialize database on startup
init_db(app)

# ----------------------------
# PUBLIC ROUTES
# ----------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-public-enquiry', methods=['POST'])
def submit_public_enquiry():
    contact_person = request.form.get('contact_person')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    customer_type = request.form.get('customer_type', 'Individual')
    fabrication_type = request.form.get('fabrication_type', 'MS Heavy Structural')
    description = request.form.get('description', '')
    project_name = request.form.get('project_name') or f"{fabrication_type} Work ({contact_person})"
    budget_estimate = float(request.form.get('budget_estimate') or 0.0)

    customer = Customer.query.filter_by(phone=phone).first()
    if not customer:
        cust_code = generate_next_code('CUST', Customer, 'customer_code')
        customer = Customer(
            customer_code=cust_code,
            customer_type=customer_type,
            contact_person=contact_person,
            phone=phone,
            email=email,
            address=description or 'Site Address Pending',
            city='Mumbai'
        )
        db.session.add(customer)
        db.session.commit()

    enq_code = generate_next_code('ENQ', Enquiry, 'enquiry_code')
    enquiry = Enquiry(
        enquiry_code=enq_code,
        customer_id=customer.id,
        project_name=project_name,
        fabrication_type=fabrication_type,
        budget_estimate=budget_estimate,
        description=description,
        status='Pending'
    )
    db.session.add(enquiry)
    db.session.commit()

    file = request.files.get('drawing_file')
    if file and file.filename != '':
        saved_path = save_uploaded_file(file, folder_sub='enquiry_drawings')
        if saved_path:
            doc = JobDocument(
                enquiry_id=enquiry.id,
                file_name=file.filename,
                file_path=saved_path,
                file_type='Drawing',
                uploaded_by=contact_person
            )
            db.session.add(doc)
            db.session.commit()

    log_audit('Public Enquiry Submitted', 'Enquiry', f'Enquiry {enq_code} by {contact_person}')
    flash(f'Requirement submitted successfully! Your Enquiry ID is {enq_code}.', 'success')
    return redirect(url_for('index'))

# ----------------------------
# AUTHENTICATION & ROLE ROUTING
# ----------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif current_user.role == 'manager':
            return redirect(url_for('manager_dashboard'))
        elif current_user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter((User.username == username) | (User.email == username)).first()
        if user and user.check_password(password):
            session.permanent = True
            login_user(user)
            log_audit('User Login Success', 'Auth', f'User @{user.username} logged in as {user.role.upper()}')
            flash(f'Welcome back, {user.full_name}! Role: {user.role.upper()}. (Auto-logout set to 15 mins inactivity)', 'success')
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'manager':
                return redirect(url_for('manager_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('staff_dashboard'))
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid username or password. Please check your credentials.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return redirect(url_for('login', tab='register'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role_name = request.form.get('role', 'customer')
        customer_type = request.form.get('customer_type', 'Individual')
        company_name = request.form.get('company_name', '')
        contact_person = request.form.get('contact_person') or username
        phone = request.form.get('phone', '')
        email = request.form.get('email') or f"{username}@fabrication.local"
        gst_number = request.form.get('gst_number', '')
        address = request.form.get('address') or 'Site Address Pending'
        city = request.form.get('city', 'Mumbai')
        state = request.form.get('state', 'Maharashtra')
        pincode = request.form.get('pincode', '')

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose another username.', 'warning')
            return redirect(url_for('login', tab='register'))

        if role_name == 'admin':
            flash('Admin accounts cannot be registered publicly.', 'danger')
            return redirect(url_for('login', tab='register'))

        if role_name == 'manager':
            manager_count = User.query.filter_by(role='manager').count()
            if manager_count >= 2:
                flash('Role Quota Exceeded: Maximum 2 Manager accounts are allowed in the system.', 'danger')
                return redirect(url_for('login', tab='register'))

        role_obj = Role.query.filter_by(name=role_name).first()
        user = User(
            username=username,
            email=email,
            full_name=contact_person,
            phone=phone,
            role=role_name,
            role_id=role_obj.id if role_obj else None,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session.permanent = True

        if role_name == 'customer':
            cust_code = generate_next_code('CUST', Customer, 'customer_code')
            customer = Customer(
                customer_code=cust_code,
                user_id=user.id,
                customer_type=customer_type,
                company_name=company_name if customer_type == 'Company' else '',
                contact_person=contact_person,
                phone=phone,
                email=email,
                gst_number=gst_number,
                address=address,
                city=city,
                state=state,
                pincode=pincode
            )
            db.session.add(customer)
            db.session.commit()
            login_user(user)
            log_audit('Customer Registration', 'Auth', f'Customer profile {cust_code} registered (@{username})')
            flash('Customer account registered successfully! Welcome to your portal.', 'success')
            return redirect(url_for('customer_dashboard'))

        elif role_name in ['manager', 'staff']:
            emp_code = generate_next_code('EMP', Employee, 'employee_code')
            emp = Employee(
                employee_code=emp_code,
                user_id=user.id,
                department='Management' if role_name == 'manager' else 'Workshop Assembly',
                designation='Project Manager' if role_name == 'manager' else 'Production Staff',
                phone=phone,
                hourly_rate=200.0 if role_name == 'manager' else 150.0
            )
            db.session.add(emp)
            db.session.commit()
            login_user(user)
            log_audit('Employee Registration', 'Auth', f'{role_name.capitalize()} account @{username} registered ({emp_code})')
            flash(f'{role_name.capitalize()} account @{username} registered successfully!', 'success')
            if role_name == 'manager':
                return redirect(url_for('manager_dashboard'))
            return redirect(url_for('staff_dashboard'))

    return render_template('register.html')

@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=15)

@app.route('/logout')
def logout():
    reason = request.args.get('reason')
    if current_user.is_authenticated:
        username = current_user.username
        log_audit('User Logout', 'Auth', f'User @{username} logged out (reason: {reason or "user_action"})')
        logout_user()
    
    session.clear()
    
    if reason == 'inactivity':
        flash('You have been automatically logged out due to 15 minutes of inactivity.', 'warning')
    elif reason in ['tab_closed', 'left_app']:
        flash('You have been automatically logged out because you exited the session or closed the browser tab.', 'info')
    else:
        flash('You have been logged out securely.', 'info')
    return redirect(url_for('login'))

# ----------------------------
# ROLE DASHBOARDS (4 ROLES)
# ----------------------------

@app.route('/dashboard/admin')
@admin_required
def admin_dashboard():
    total_enquiries = Enquiry.query.count()
    total_quotations = Quotation.query.count()
    active_jobs = JobOrder.query.filter(JobOrder.status.in_(['Approved', 'Production', 'Ready', 'Delivered', 'Installed'])).count()
    
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity_in_stock <= InventoryItem.reorder_level).all()
    low_stock_count = len(low_stock_items)

    total_customers = Customer.query.count()
    open_tickets_count = ServiceTicket.query.filter_by(status='Open').count()

    jobs = JobOrder.query.all()
    total_revenue = sum(j.total_contract_value for j in jobs)
    
    invoices = Invoice.query.all()
    total_pending_dues = sum(inv.balance_amount for inv in invoices)

    recent_jobs = JobOrder.query.order_by(JobOrder.id.desc()).limit(5).all()
    recent_enquiries = Enquiry.query.order_by(Enquiry.id.desc()).limit(5).all()

    return render_template('dashboard/admin_dashboard.html',
        total_enquiries=total_enquiries,
        total_quotations=total_quotations,
        active_jobs=active_jobs,
        low_stock_count=low_stock_count,
        total_customers=total_customers,
        open_tickets_count=open_tickets_count,
        total_revenue=total_revenue,
        total_pending_dues=total_pending_dues,
        recent_jobs=recent_jobs,
        recent_enquiries=recent_enquiries,
        inventory_alerts=low_stock_items
    )

@app.route('/dashboard/manager')
@staff_required
def manager_dashboard():
    total_enquiries = Enquiry.query.count()
    total_quotations = Quotation.query.count()
    active_jobs = JobOrder.query.filter(JobOrder.status.in_(['Approved', 'Production', 'Ready', 'Delivered', 'Installed'])).count()
    total_customers = Customer.query.count()
    recent_jobs = JobOrder.query.order_by(JobOrder.id.desc()).limit(5).all()

    return render_template('dashboard/manager_dashboard.html',
        total_enquiries=total_enquiries,
        total_quotations=total_quotations,
        active_jobs=active_jobs,
        total_customers=total_customers,
        recent_jobs=recent_jobs
    )

@app.route('/dashboard/staff')
@login_required
def staff_dashboard():
    if current_user.role not in ['staff', 'admin', 'manager']:
        flash('Access restricted to workshop staff.', 'danger')
        return redirect(url_for('login'))

    assigned_cards = JobCard.query.filter_by(assigned_staff_id=current_user.id).all()
    active_jobs = JobOrder.query.filter(JobOrder.status.in_(['Approved', 'Production', 'Ready'])).all()
    return render_template('dashboard/staff_dashboard.html', assigned_cards=assigned_cards, active_jobs=active_jobs)

@app.route('/dashboard/customer')
@login_required
def customer_dashboard():
    customer = Customer.query.filter_by(user_id=current_user.id).first()
    if not customer:
        customer = Customer.query.filter_by(email=current_user.email).first()
    
    if not customer:
        flash('Customer profile not found. Please contact administration.', 'warning')
        return redirect(url_for('index'))

    return render_template('dashboard/customer_dashboard.html', customer=customer)

# ----------------------------
# MODULE: STAFF JOB CARDS
# ----------------------------

@app.route('/update-job-card-status/<int:card_id>', methods=['POST'])
@login_required
def update_job_card_status(card_id):
    card = JobCard.query.get_or_404(card_id)
    card.status = request.form.get('status')
    card.completion_pct = int(request.form.get('completion_pct') or 0)
    db.session.commit()
    log_audit('Job Card Updated', 'JobCard', f'Card {card.card_code} set to {card.status} ({card.completion_pct}%)')
    flash(f'Job Card {card.card_code} updated successfully.', 'success')
    return redirect(url_for('staff_dashboard'))

# ----------------------------
# MODULE: CUSTOMER MANAGEMENT
# ----------------------------

@app.route('/customers', methods=['GET', 'POST'])
@staff_required
def customers_list():
    if request.method == 'POST':
        cust_code = generate_next_code('CUST', Customer, 'customer_code')
        customer = Customer(
            customer_code=cust_code,
            customer_type=request.form.get('customer_type', 'Individual'),
            company_name=request.form.get('company_name'),
            contact_person=request.form.get('contact_person'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            gst_number=request.form.get('gst_number'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state', 'Maharashtra'),
            pincode=request.form.get('pincode'),
            site_addresses=request.form.get('site_addresses')
        )
        db.session.add(customer)
        db.session.commit()
        log_audit('Customer Profile Created', 'Customer', f'Code {cust_code}')
        flash(f'Customer {customer.contact_person} registered with Code {cust_code}.', 'success')
        return redirect(url_for('customers_list'))

    customers = Customer.query.order_by(Customer.id.desc()).all()
    return render_template('modules/customers.html', customers=customers)

# ----------------------------
# MODULE: ENQUIRY & SITE VISITS
# ----------------------------

@app.route('/enquiries', methods=['GET', 'POST'])
@staff_required
def enquiries_list():
    if request.method == 'POST':
        enq_code = generate_next_code('ENQ', Enquiry, 'enquiry_code')
        enquiry = Enquiry(
            enquiry_code=enq_code,
            customer_id=int(request.form.get('customer_id')),
            project_name=request.form.get('project_name'),
            fabrication_type=request.form.get('fabrication_type'),
            project_category=request.form.get('project_category', 'Commercial'),
            site_location=request.form.get('site_location'),
            description=request.form.get('description'),
            budget_estimate=float(request.form.get('budget_estimate') or 0.0),
            status='Pending'
        )
        db.session.add(enquiry)
        db.session.commit()
        log_audit('Enquiry Recorded', 'Enquiry', f'Code {enq_code}')
        flash(f'Enquiry {enq_code} recorded successfully.', 'success')
        return redirect(url_for('enquiries_list'))

    enquiries = Enquiry.query.order_by(Enquiry.id.desc()).all()
    customers = Customer.query.all()
    return render_template('modules/enquiries.html', enquiries=enquiries, customers=customers)

# ----------------------------
# MODULE: ESTIMATION & QUOTATIONS
# ----------------------------

@app.route('/quotation-builder')
@staff_required
def quotation_builder():
    enquiry_id = request.args.get('enquiry_id')
    selected_enquiry = Enquiry.query.get(enquiry_id) if enquiry_id else None

    customers = Customer.query.all()
    enquiries = Enquiry.query.all()
    default_valid_date = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')

    return render_template('modules/quotation_builder.html',
        customers=customers,
        enquiries=enquiries,
        selected_enquiry=selected_enquiry,
        default_valid_date=default_valid_date
    )

@app.route('/save-quotation', methods=['POST'])
@staff_required
def save_quotation():
    customer_id = int(request.form.get('customer_id'))
    enquiry_id = request.form.get('enquiry_id')
    enquiry_id = int(enquiry_id) if enquiry_id else None
    
    valid_until_str = request.form.get('valid_until')
    valid_until = datetime.strptime(valid_until_str, '%Y-%m-%d').date() if valid_until_str else date.today() + timedelta(days=15)

    material_cost = float(request.form.get('material_cost') or 0.0)
    labour_cost = float(request.form.get('labour_cost') or 0.0)
    machining_cutting_cost = float(request.form.get('machining_cutting_cost') or 0.0)
    finishing_painting_cost = float(request.form.get('finishing_painting_cost') or 0.0)
    transportation_cost = float(request.form.get('transportation_cost') or 0.0)
    installation_cost = float(request.form.get('installation_cost') or 0.0)
    wastage_cost = float(request.form.get('wastage_cost') or 0.0)
    gst_rate = float(request.form.get('gst_rate') or 18.0)

    subtotal = material_cost + labour_cost + machining_cutting_cost + finishing_painting_cost + transportation_cost + installation_cost + wastage_cost
    gst_amount = (subtotal * gst_rate) / 100.0
    total_amount = subtotal + gst_amount

    quote_code = generate_next_code('QT', Quotation, 'quote_code')
    quotation = Quotation(
        quote_code=quote_code,
        customer_id=customer_id,
        enquiry_id=enquiry_id,
        valid_until=valid_until,
        material_cost=material_cost,
        labour_cost=labour_cost,
        machining_cutting_cost=machining_cutting_cost,
        finishing_painting_cost=finishing_painting_cost,
        transportation_cost=transportation_cost,
        installation_cost=installation_cost,
        wastage_cost=wastage_cost,
        subtotal=subtotal,
        gst_rate=gst_rate,
        gst_amount=gst_amount,
        total_amount=total_amount,
        status='Sent',
        created_by=current_user.full_name
    )
    db.session.add(quotation)
    db.session.commit()

    item_names = request.form.getlist('item_name[]')
    material_types = request.form.getlist('material_type[]')
    material_grades = request.form.getlist('material_grade[]')
    thicknesses = request.form.getlist('thickness_mm[]')
    lengths = request.form.getlist('length_mm[]')
    widths = request.form.getlist('width_mm[]')
    weights = request.form.getlist('weight_kg[]')
    quantities = request.form.getlist('quantity[]')
    total_prices = request.form.getlist('total_price[]')
    welding_details_list = request.form.getlist('welding_details[]')
    finishing_details_list = request.form.getlist('finishing_details[]')
    painting_details_list = request.form.getlist('painting_details[]')

    for i in range(len(item_names)):
        if item_names[i].strip():
            qi = QuotationItem(
                quotation_id=quotation.id,
                item_name=item_names[i],
                material_type=material_types[i] if i < len(material_types) else 'MS',
                material_grade=material_grades[i] if i < len(material_grades) else '',
                thickness_mm=float(thicknesses[i]) if i < len(thicknesses) and thicknesses[i] else 0.0,
                length_mm=float(lengths[i]) if i < len(lengths) and lengths[i] else 0.0,
                width_mm=float(widths[i]) if i < len(widths) and widths[i] else 0.0,
                weight_kg=float(weights[i]) if i < len(weights) and weights[i] else 0.0,
                quantity=int(quantities[i]) if i < len(quantities) and quantities[i] else 1,
                total_price=float(total_prices[i]) if i < len(total_prices) and total_prices[i] else 0.0,
                welding_details=welding_details_list[i] if i < len(welding_details_list) else '',
                finishing_details=finishing_details_list[i] if i < len(finishing_details_list) else '',
                painting_details=painting_details_list[i] if i < len(painting_details_list) else ''
            )
            db.session.add(qi)

    if enquiry_id:
        enq = Enquiry.query.get(enquiry_id)
        if enq:
            enq.status = 'Quotation Generated'

    db.session.commit()
    log_audit('Quotation Generated', 'Quotation', f'Code {quote_code} total ₹{total_amount}')
    flash(f'Quotation {quote_code} generated and saved successfully!', 'success')
    return redirect(url_for('view_quotation', quote_id=quotation.id))

@app.route('/quotations')
@staff_required
def quotations_list():
    quotations = Quotation.query.order_by(Quotation.id.desc()).all()
    return render_template('modules/quotations_list.html', quotations=quotations)

@app.route('/quotation/<int:quote_id>')
def view_quotation(quote_id):
    quotation = Quotation.query.get_or_404(quote_id)
    return render_template('modules/view_quotation.html', quotation=quotation)

@app.route('/convert-quote-to-job/<int:quote_id>')
@staff_required
def convert_quote_to_job(quote_id):
    quotation = Quotation.query.get_or_404(quote_id)
    quotation.status = 'Approved'

    job_code = generate_next_code('JOB', JobOrder, 'job_code')
    job = JobOrder(
        job_code=job_code,
        quotation_id=quotation.id,
        customer_id=quotation.customer_id,
        project_name=quotation.enquiry.project_name if quotation.enquiry else f"Fabrication Order {quotation.quote_code}",
        status='Approved',
        priority='High',
        start_date=date.today(),
        target_completion_date=date.today() + timedelta(days=25),
        site_address=f"{quotation.customer.address}, {quotation.customer.city}",
        total_contract_value=quotation.total_amount,
        balance_due=quotation.total_amount
    )
    db.session.add(job)
    db.session.commit()

    stages_data = [
        ('Design & CAD Drawing Approval', 1),
        ('Material Cutting & Sizing', 2),
        ('MIG/TIG Welding & Frame Assembly', 3),
        ('Grinding & Drilling Bolt Holes', 4),
        ('Epoxy Painting & Surface Finish', 5),
        ('Quality Check & Dimensions Audit', 6),
        ('On-Site Transport & Erection', 7)
    ]
    for name, seq in stages_data:
        stage = ProductionStage(job_id=job.id, stage_name=name, sequence_order=seq, status='Pending', completion_pct=0)
        db.session.add(stage)

    if quotation.enquiry:
        quotation.enquiry.status = 'Converted to Order'

    db.session.commit()
    log_audit('Work Order Converted', 'Job', f'Job {job_code} from Quote {quotation.quote_code}')
    flash(f'Quotation approved! Work Order {job_code} generated automatically.', 'success')
    return redirect(url_for('job_detail', job_id=job.id))

# ----------------------------
# MODULE: WORK ORDERS & PRODUCTION
# ----------------------------

@app.route('/jobs')
@staff_required
def jobs_list():
    jobs = JobOrder.query.order_by(JobOrder.id.desc()).all()
    customers = Customer.query.all()
    return render_template('modules/jobs.html', jobs=jobs, customers=customers)

@app.route('/create-job-direct', methods=['POST'])
@staff_required
def create_job_direct():
    job_code = generate_next_code('JOB', JobOrder, 'job_code')
    job = JobOrder(
        job_code=job_code,
        customer_id=int(request.form.get('customer_id')),
        project_name=request.form.get('project_name'),
        total_contract_value=float(request.form.get('total_contract_value') or 0.0),
        site_address=request.form.get('site_address'),
        status='Approved',
        start_date=date.today()
    )
    db.session.add(job)
    db.session.commit()

    stages_data = ['Design & CAD Approval', 'Material Cutting', 'Welding & Assembly', 'Grinding & Drilling', 'Painting', 'Quality Check', 'Site Erection']
    for seq, name in enumerate(stages_data, 1):
        stage = ProductionStage(job_id=job.id, stage_name=name, sequence_order=seq, status='Pending')
        db.session.add(stage)

    db.session.commit()
    log_audit('Work Order Created', 'Job', f'Code {job_code}')
    flash(f'Work Order {job_code} created.', 'success')
    return redirect(url_for('job_detail', job_id=job.id))

@app.route('/job/<int:job_id>')
@login_required
def job_detail(job_id):
    job = JobOrder.query.get_or_404(job_id)
    return render_template('modules/job_detail.html', job=job)

@app.route('/update-job-status/<int:job_id>', methods=['POST'])
@staff_required
def update_job_status(job_id):
    job = JobOrder.query.get_or_404(job_id)
    job.status = request.form.get('status')
    db.session.commit()
    log_audit('Job Status Updated', 'Job', f'Job {job.job_code} set to {job.status}')
    flash(f'Job {job.job_code} status updated to {job.status}.', 'success')
    return redirect(url_for('job_detail', job_id=job.id))

@app.route('/update-production-stage/<int:stage_id>', methods=['POST'])
@staff_required
def update_production_stage(stage_id):
    stage = ProductionStage.query.get_or_404(stage_id)
    stage.status = request.form.get('status')
    stage.completion_pct = int(request.form.get('completion_pct') or 0)
    db.session.commit()
    flash(f'Stage "{stage.stage_name}" updated.', 'success')
    return redirect(url_for('job_detail', job_id=stage.job_id))

@app.route('/upload-job-document/<int:job_id>', methods=['POST'])
@login_required
def upload_job_document(job_id):
    job = JobOrder.query.get_or_404(job_id)
    file = request.files.get('file')
    file_type = request.form.get('file_type', 'Drawing')

    if file and file.filename != '':
        saved_path = save_uploaded_file(file, folder_sub='job_photos')
        if saved_path:
            doc = JobDocument(
                job_id=job.id,
                file_name=file.filename,
                file_path=saved_path,
                file_type=file_type,
                uploaded_by=current_user.full_name
            )
            db.session.add(doc)
            db.session.commit()
            log_audit('Job Photo Uploaded', 'Document', f'File {file.filename} for Job {job.job_code}')
            flash('File uploaded successfully.', 'success')
    return redirect(url_for('job_detail', job_id=job.id))

@app.route('/log-job-labour/<int:job_id>', methods=['POST'])
@staff_required
def log_job_labour(job_id):
    worker_name = request.form.get('worker_name')
    hours_worked = float(request.form.get('hours_worked') or 0.0)
    hourly_rate = float(request.form.get('hourly_rate') or 0.0)
    total_cost = hours_worked * hourly_rate

    log = JobLabourLog(
        job_id=job_id,
        worker_name=worker_name,
        hours_worked=hours_worked,
        hourly_rate=hourly_rate,
        total_cost=total_cost,
        work_date=date.today()
    )
    db.session.add(log)
    db.session.commit()
    flash('Labour log added.', 'success')
    return redirect(url_for('job_detail', job_id=job_id))

# ----------------------------
# MODULE: INVENTORY & STOCK
# ----------------------------

@app.route('/inventory', methods=['GET', 'POST'])
@staff_required
def inventory_list():
    if request.method == 'POST':
        item_code = generate_next_code('MAT', InventoryItem, 'item_code')
        item = InventoryItem(
            item_code=item_code,
            item_name=request.form.get('item_name'),
            category=request.form.get('category'),
            material_type=request.form.get('material_type'),
            unit=request.form.get('unit', 'Kg'),
            unit_cost=float(request.form.get('unit_cost') or 0.0),
            quantity_in_stock=float(request.form.get('quantity_in_stock') or 0.0),
            reorder_level=float(request.form.get('reorder_level') or 10.0)
        )
        db.session.add(item)
        db.session.commit()
        log_audit('Inventory Item Added', 'Inventory', f'Item {item.item_name} ({item_code})')
        flash(f'Material {item.item_name} added.', 'success')
        return redirect(url_for('inventory_list'))

    items = InventoryItem.query.all()
    return render_template('modules/inventory.html', items=items)

# ----------------------------
# MODULE: BILLING & GST INVOICES
# ----------------------------

@app.route('/billing')
@staff_required
def billing_list():
    invoices = Invoice.query.order_by(Invoice.id.desc()).all()
    jobs = JobOrder.query.all()
    return render_template('modules/billing.html', invoices=invoices, jobs=jobs)

@app.route('/create-invoice', methods=['POST'])
@staff_required
def create_invoice():
    job_id = int(request.form.get('job_id'))
    job = JobOrder.query.get_or_404(job_id)
    billing_type = request.form.get('billing_type', 'Advance')
    subtotal = float(request.form.get('subtotal') or 0.0)
    gst_rate = 18.0
    gst_amount = (subtotal * gst_rate) / 100.0
    total_amount = subtotal + gst_amount

    inv_code = generate_next_code('INV', Invoice, 'invoice_code')
    invoice = Invoice(
        invoice_code=inv_code,
        job_id=job.id,
        customer_id=job.customer_id,
        invoice_date=date.today(),
        billing_type=billing_type,
        subtotal=subtotal,
        gst_rate=gst_rate,
        gst_amount=gst_amount,
        total_amount=total_amount,
        balance_amount=total_amount,
        payment_status='Unpaid'
    )
    db.session.add(invoice)
    db.session.commit()
    log_audit('Tax Invoice Created', 'Billing', f'Code {inv_code} total ₹{total_amount}')
    flash(f'GST Invoice {inv_code} created.', 'success')
    return redirect(url_for('billing_list'))

@app.route('/record-payment', methods=['POST'])
@staff_required
def record_payment():
    invoice_id = int(request.form.get('invoice_id'))
    invoice = Invoice.query.get_or_404(invoice_id)
    amount = float(request.form.get('amount') or 0.0)
    payment_mode = request.form.get('payment_mode')
    reference_no = request.form.get('reference_no')

    pay_code = generate_next_code('PAY', Payment, 'payment_code')
    payment = Payment(
        payment_code=pay_code,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        payment_date=date.today(),
        amount=amount,
        payment_mode=payment_mode,
        reference_no=reference_no
    )
    db.session.add(payment)

    invoice.paid_amount += amount
    invoice.balance_amount = max(0.0, invoice.total_amount - invoice.paid_amount)
    if invoice.balance_amount <= 0:
        invoice.payment_status = 'Paid'
    else:
        invoice.payment_status = 'Partially Paid'

    db.session.commit()
    log_audit('Payment Credit Recorded', 'Billing', f'Payment {pay_code} amount ₹{amount}')
    flash(f'Payment of ₹{amount:,.2f} recorded.', 'success')
    return redirect(url_for('billing_list'))

# ----------------------------
# MODULE: SERVICE TICKETS
# ----------------------------

@app.route('/service-tickets')
@login_required
def service_tickets_list():
    if current_user.role in ['admin', 'manager', 'supervisor']:
        tickets = ServiceTicket.query.order_by(ServiceTicket.id.desc()).all()
    else:
        cust = Customer.query.filter_by(user_id=current_user.id).first()
        tickets = ServiceTicket.query.filter_by(customer_id=cust.id).all() if cust else []
    return render_template('modules/service_tickets.html', tickets=tickets)

@app.route('/create-service-ticket', methods=['POST'])
@login_required
def create_service_ticket():
    cust = Customer.query.filter_by(user_id=current_user.id).first()
    if not cust:
        flash('Customer profile not found.', 'danger')
        return redirect(url_for('customer_dashboard'))

    ticket_code = generate_next_code('SR', ServiceTicket, 'ticket_code')
    ticket = ServiceTicket(
        ticket_code=ticket_code,
        customer_id=cust.id,
        title=request.form.get('title'),
        description=request.form.get('description'),
        status='Open',
        priority='Medium'
    )
    db.session.add(ticket)
    db.session.commit()
    log_audit('Service Ticket Created', 'Service', f'Code {ticket_code}')
    flash(f'Service ticket {ticket_code} created successfully.', 'success')
    return redirect(url_for('customer_dashboard'))

@app.route('/update-ticket-status/<int:ticket_id>', methods=['POST'])
@staff_required
def update_ticket_status(ticket_id):
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    ticket.status = request.form.get('status')
    db.session.commit()
    flash('Ticket status updated.', 'success')
    return redirect(url_for('service_tickets_list'))

# ----------------------------
# MODULE: AUDIT LOGS & REPORTS
# ----------------------------

@app.route('/audit-logs')
@admin_required
def audit_logs_view():
    logs = AuditLog.query.order_by(AuditLog.id.desc()).limit(100).all()
    return render_template('modules/audit_logs.html', logs=logs)

@app.route('/reports')
@staff_required
def reports_view():
    jobs = JobOrder.query.all()
    total_contract_value = sum(j.total_contract_value for j in jobs)
    total_profit = total_contract_value * 0.225

    payments = Payment.query.all()
    total_received = sum(p.amount for p in payments)

    invoices = Invoice.query.all()
    total_pending = sum(inv.balance_amount for inv in invoices)

    return render_template('modules/reports.html',
        jobs=jobs,
        total_contract_value=total_contract_value,
        total_profit=total_profit,
        total_received=total_received,
        total_pending=total_pending
    )

# ----------------------------
# MODULE: ADMIN USER SECURITY & RBAC
# ----------------------------

@app.route('/admin/users', methods=['GET', 'POST'])
@admin_required
def admin_users_list():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        role_name = request.form.get('role', 'staff')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different username.', 'warning')
            return redirect(url_for('admin_users_list'))

        # Strict Role Limits Enforcement: 1 Admin max, 2 Managers max, Multiple Staff, Multiple Customers
        if role_name == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count >= 1:
                flash('Security Policy Violation: Maximum 1 Master Admin account is allowed in the system. You cannot create another admin account.', 'danger')
                return redirect(url_for('admin_users_list'))

        if role_name == 'manager':
            manager_count = User.query.filter_by(role='manager').count()
            if manager_count >= 2:
                flash('Role Quota Exceeded: Maximum 2 Manager accounts are allowed in the system. You cannot create more than 2 managers.', 'danger')
                return redirect(url_for('admin_users_list'))

        role_obj = Role.query.filter_by(name=role_name).first()

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role_name,
            role_id=role_obj.id if role_obj else None,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role_name in ['manager', 'staff']:
            emp_code = generate_next_code('EMP', Employee, 'employee_code')
            emp = Employee(
                employee_code=emp_code,
                user_id=user.id,
                department='Management' if role_name == 'manager' else 'Workshop Assembly',
                designation='Project Manager' if role_name == 'manager' else 'Production Staff',
                phone=phone,
                hourly_rate=200.0 if role_name == 'manager' else 150.0
            )
            db.session.add(emp)
            db.session.commit()
        elif role_name == 'customer':
            cust_code = generate_next_code('CUST', Customer, 'customer_code')
            customer = Customer(
                customer_code=cust_code,
                user_id=user.id,
                customer_type='Individual',
                contact_person=full_name,
                phone=phone,
                email=email,
                address='Site Address Pending',
                city='Mumbai'
            )
            db.session.add(customer)
            db.session.commit()

        log_audit('User Account Created', 'Auth', f'User @{username} ({role_name.upper()})')
        flash(f'Account @{username} ({role_name.upper()}) created successfully with encrypted password.', 'success')
        return redirect(url_for('admin_users_list'))

    users = User.query.order_by(User.id.asc()).all()
    admin_count = User.query.filter_by(role='admin').count()
    manager_count = User.query.filter_by(role='manager').count()
    staff_count = User.query.filter_by(role='staff').count()
    customer_count = User.query.filter_by(role='customer').count()

    return render_template('modules/user_management.html',
        users=users,
        admin_count=admin_count,
        manager_count=manager_count,
        staff_count=staff_count,
        customer_count=customer_count
    )

@app.route('/admin/reset-password', methods=['POST'])
@admin_required
def admin_reset_password():
    user_id = int(request.form.get('user_id'))
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    user.set_password(new_password)
    db.session.commit()
    log_audit('User Password Reset', 'Auth', f'Password reset for @{user.username}')
    flash(f'Encrypted password for @{user.username} updated successfully.', 'success')
    return redirect(url_for('admin_users_list'))

@app.route('/customer/approve-quote/<int:quote_id>')
@login_required
def customer_approve_quote(quote_id):
    quotation = Quotation.query.get_or_404(quote_id)
    quotation.status = 'Approved'

    job_code = generate_next_code('JOB', JobOrder, 'job_code')
    job = JobOrder(
        job_code=job_code,
        quotation_id=quotation.id,
        customer_id=quotation.customer_id,
        project_name=quotation.enquiry.project_name if quotation.enquiry else f"Fabrication Order {quotation.quote_code}",
        status='Approved',
        priority='High',
        start_date=date.today(),
        target_completion_date=date.today() + timedelta(days=25),
        site_address=f"{quotation.customer.address}, {quotation.customer.city}",
        total_contract_value=quotation.total_amount,
        balance_due=quotation.total_amount
    )
    db.session.add(job)

    stages_data = [
        ('Design & CAD Drawing Approval', 1),
        ('Material Cutting & Sizing', 2),
        ('MIG/TIG Welding & Frame Assembly', 3),
        ('Grinding & Drilling Bolt Holes', 4),
        ('Epoxy Painting & Surface Finish', 5),
        ('Quality Check & Dimensions Audit', 6),
        ('On-Site Transport & Erection', 7)
    ]
    for name, seq in stages_data:
        stage = ProductionStage(job_id=job.id, stage_name=name, sequence_order=seq, status='Pending', completion_pct=0)
        db.session.add(stage)

    if quotation.enquiry:
        quotation.enquiry.status = 'Converted to Order'

    db.session.commit()
    log_audit('Quotation Approved Online', 'Quotation', f'Customer approved Quote {quotation.quote_code}')
    flash(f'Quotation {quotation.quote_code} accepted & approved online! Work Order {job_code} created.', 'success')
    return redirect(url_for('customer_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
