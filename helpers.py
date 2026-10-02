import os
import uuid
from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from config import Config

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Encrypted Admin authorization required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager']:
            flash('Access denied. Manager or Admin authorization required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'manager', 'staff']:
            flash('Access restricted to authorized fabrication staff.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_uploaded_file(file_obj, folder_sub='drawings'):
    if not file_obj or file_obj.filename == '':
        return None
    
    if allowed_file(file_obj.filename):
        filename = secure_filename(file_obj.filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        target_dir = os.path.join(Config.UPLOAD_FOLDER, folder_sub)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, unique_name)
        file_obj.save(filepath)
        # Return web accessible path relative to static
        return f"uploads/{folder_sub}/{unique_name}"
    return None

def generate_next_code(prefix, model, field_name):
    """
    Generates codes like CUST-1005, ENQ-2003, QT-3004, JOB-4002, etc.
    """
    from models import db
    last_record = db.session.query(getattr(model, field_name)).order_by(model.id.desc()).first()
    if not last_record:
        return f"{prefix}-1001"
    
    last_code = getattr(last_record, field_name)
    try:
        parts = last_code.split('-')
        num = int(parts[1]) + 1
        return f"{prefix}-{num}"
    except Exception:
        return f"{prefix}-{uuid.uuid4().hex[:4].upper()}"
