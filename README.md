# 🏗️ Apex Fabrication Customer Management System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0%2B-black?logo=flask)
![MySQL](https://img.shields.io/badge/MySQL-WAMP-orange?logo=mysql)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-blueviolet?logo=tailwindcss)
![License](https://img.shields.io/badge/License-MIT-green)

A modern, clean, production-grade **Fabrication & Heavy Engineering Customer Management System** built with **Python Flask**, **SQLAlchemy**, **MySQL (WAMP Server)**, **Tailwind CSS**, and **Bootstrap**. 

Designed specifically for custom steel, aluminium, and sheet metal fabrication workshops to streamline customer enquiries, quotations, work orders, shop-floor job cards, inventory stock, invoicing, and security.

---

## 🌟 Key Features & Improvements

* **Clean & Simplified Forms**:
  * **Unified 2-Tab Login & Registration**: Minimal 5-field registration form (Role, Full Name, Phone, Username, Password) without any cluttered demo login cards or unnecessary inputs.
  * **Simplified Requirement Form**: Quick 4-field public enquiry submission (Name, Phone, Fabrication Type, Details) with optional drawing file upload.
* **4-Tier Role-Based Access Control (RBAC)**:
  1. 🛡️ **Master Admin**: Full system control, user security, audit logs, and analytics dashboard. *(Strict Quota: Max 1 Admin)*
  2. 💼 **Manager**: Enquiries, site visits, quotations, work orders, and stock allocation. *(Strict Quota: Max 2 Managers)*
  3. 👷 **Staff**: Shop-floor production staff with assigned job cards, stage progress updates, and labour logs.
  4. 👤 **Customer**: Self-service portal to submit requirements, track quotation status, view live progress, and manage invoices.
* **Automatic Security & Auto-Logout**:
  * ⏱️ **15-Minute Inactivity Timeout**: Automatically logs out idle user sessions across all roles.
  * 🚪 **Tab Exit & Browser Close Logout**: Automatically invalidates session tokens if the user closes the browser tab or window.
* **Full Fabrication Lifecycle Workflow**:
  `Enquiry` ➔ `Site Visit & Measurements` ➔ `Quotation` ➔ `Work Order` ➔ `Job Cards & Stages` ➔ `Stock Deduction` ➔ `Invoicing & Payments`
* **Real-time Stock Management**: Tracks raw sheets, pipes, beams, and consumables with automatic reorder alerts.
* **Audit & Security Logging**: Tracks all critical user actions, logins, registration, and status updates.

---

## 🛠️ Technology Stack

| Component | Technology Used |
| :--- | :--- |
| **Backend Framework** | Python 3.10+, Flask 3.0+ |
| **Database** | MySQL (WAMP Server) via PyMySQL & Flask-SQLAlchemy |
| **Authentication** | Flask-Login, Werkzeug Security (Scrypt Hashing) |
| **Frontend Styling** | Tailwind CSS (CDN), Bootstrap 5 Utilities |
| **Icons & Visuals** | FontAwesome 6, Lucide Icons, Chart.js |
| **Environment** | python-dotenv |

---

## 🔐 Security & Role Quotas

1. **Password Security**: All user passwords are encrypted using salted Scrypt hashes.
2. **Session Cookies**: Scoped with `SESSION_COOKIE_HTTPONLY=True` and `SESSION_COOKIE_SAMESITE='Lax'`.
3. **Role Quota Constraints**:
   * **Admin**: Maximum 1 active account (`admin`). Cannot be selected during registration.
   * **Manager**: Maximum 2 active accounts.
   * **Staff & Customer**: Unlimited with automatic `EMP-XXXX` and `CUST-XXXX` profile generation.

---

## 📁 Project Structure

```
Fabrication Customer Management System/
│
├── app.py                   # Main Flask application & route controllers
├── config.py                # System settings, session lifetimes, DB URIs
├── database.py              # WAMP MySQL auto-creation & table initializer
├── database_setup.sql       # Pure SQL dump file for direct phpMyAdmin import
├── helpers.py               # RBAC decorators, secure upload & code generators
├── models.py                # 26 SQLAlchemy database models & schemas
├── requirements.txt         # Python dependencies
├── test_system.py           # Automated test suite (8 tests)
├── .env.example             # Environment template
├── README.md                # Documentation for GitHub
│
├── static/
│   └── uploads/             # CAD drawings & document uploads
│
└── templates/
    ├── base.html            # Core layout with auto-logout scripts
    ├── index.html           # Public landing & requirement submission
    ├── login.html           # Unified 2-tab login & registration
    └── modules/             # Role dashboards, quotations, inventory, billing
```

---

## 🚀 Quick Setup & Installation Guide

### Prerequisites
* **Python 3.10+** installed
* **WAMP Server** (or XAMPP / standalone MySQL) running on `localhost:3306`

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/fabrication-management-system.git
cd fabrication-management-system
```

### Step 2: Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure WAMP MySQL is running. Default database configuration:
```env
SECRET_KEY=replace-with-a-random-secret-key
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=fabrication_management
MYSQL_PORT=3306
```

### Step 4: Database Initialization
The application automatically checks and creates the MySQL database `fabrication_management` on startup. 

*Alternative (Manual SQL Import)*: You can also import `database_setup.sql` into **phpMyAdmin** directly.

### Step 5: Run the Application
```bash
python app.py
```
Open your browser and navigate to `http://127.0.0.1:5000/`.

---

## 🔑 Default Master Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Master Admin** | `admin` | `admin123` | Master System Access |

*Managers, Staff, and Customers can be registered directly via the `/login` registration tab.*

---

## 🧪 Running Automated Tests

To run the full automated test suite:
```bash
python test_system.py
```

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
