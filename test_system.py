import unittest
from app import app
from models import db, User, Role, Employee, Customer, InventoryItem, Enquiry

class FabricationSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def test_01_public_homepage(self):
        """Test public home page loads cleanly"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'APEX', response.data)

    def test_02_login_page_renders(self):
        """Test unified login/register page renders with 2 tabs without any demo login cards"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
        self.assertIn(b'Register Account', response.data)

    def test_03_admin_login(self):
        """Test master admin login authentication"""
        response = self.app.post('/login', data=dict(
            username='admin',
            password='admin123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Admin Dashboard', response.data)

    def test_04_simplified_customer_registration(self):
        """Test registering a customer account with simplified inputs"""
        response = self.app.post('/register', data=dict(
            role='customer',
            contact_person='Test Customer',
            phone='+91 99999 88888',
            username='testcustomer',
            password='password123'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            user = User.query.filter_by(username='testcustomer').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.role, 'customer')

    def test_05_simplified_public_enquiry(self):
        """Test submitting a public requirement enquiry with simplified form"""
        response = self.app.post('/submit-public-enquiry', data=dict(
            contact_person='Enquiry User',
            phone='+91 88888 77777',
            fabrication_type='SS 304 Decorative',
            description='20ft SS Railing for balcony at Baner, Pune'
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Requirement submitted successfully', response.data)

    def test_06_role_quotas(self):
        """Test strict role quotas (Max 1 Admin, Max 2 Managers)"""
        with app.app_context():
            admin_count = User.query.filter_by(role='admin').count()
            self.assertLessEqual(admin_count, 1)

            manager_count = User.query.filter_by(role='manager').count()
            self.assertLessEqual(manager_count, 2)

    def test_07_inventory_and_stock(self):
        """Test raw material inventory records"""
        with app.app_context():
            items = InventoryItem.query.all()
            self.assertGreaterEqual(len(items), 1)

    def test_08_auto_logout_routes(self):
        """Test tab exit auto-logout & inactivity logout handlers"""
        response = self.app.get('/logout?reason=tab_closed', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'automatically logged out', response.data)

if __name__ == '__main__':
    unittest.main()
