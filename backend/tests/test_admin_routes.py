"""Smoke tests for routes_admin/ endpoints (requires admin token)"""
import pytest


# ---- catalog.py ----
class TestCatalog:
    def test_get_categories(self, client, staff_token):
        r = client.get('/api/v1/console/admin/categories', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_get_product_types(self, client, staff_token):
        r = client.get('/api/v1/console/admin/product-types', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_brands(self, client, staff_token):
        r = client.get('/api/v1/console/admin/brands', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_models(self, client, staff_token):
        r = client.get('/api/v1/console/admin/models', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_create_category(self, client, staff_token):
        r = client.post('/api/v1/console/admin/categories',
            json={'name': 'TestCat'},
            headers={'X-Staff-Token': staff_token})
        assert r.status_code in (200, 201)

    def test_create_brand(self, client, staff_token):
        r = client.post('/api/v1/console/admin/brands',
            json={'name': 'TestBrand'},
            headers={'X-Staff-Token': staff_token})
        assert r.status_code in (200, 201)

    def test_get_brand_models_filter(self, client, staff_token):
        r = client.get('/api/v1/console/admin/models?brand_id=1', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_no_admin_token_rejected(self, client):
        r = client.get('/api/v1/console/admin/categories')
        assert r.status_code == 403


# ---- services.py ----
class TestServices:
    def test_get_service_types(self, client, staff_token):
        r = client.get('/api/v1/console/admin/service-types', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_service_items(self, client, staff_token):
        r = client.get('/api/v1/console/admin/service-items', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_special_services(self, client, staff_token):
        r = client.get('/api/v1/console/admin/special-services', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200


# ---- staff.py ----
class TestStaff:
    def test_get_staff(self, client, staff_token):
        r = client.get('/api/v1/console/admin/staff', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200
    def test_create_staff(self, client, staff_token):
        r = client.post('/api/v1/console/admin/staff',
            json={'username': 'newuser', 'password': 'pass123456', 'full_name': 'New User', 'role': 'technician'},
            headers={'X-Staff-Token': staff_token})
        assert r.status_code in (200, 201, 409, 400)


# ---- pricing.py ----
class TestPricing:
    def test_get_prices(self, client, staff_token):
        r = client.get('/api/v1/console/admin/prices', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200


# ---- customers.py ----
class TestCustomers:
    def test_get_customers(self, client, staff_token):
        r = client.get('/api/v1/console/admin/customers', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_customers_list(self, client, staff_token):
        r = client.get('/api/v1/console/admin/customers/list', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_customer_by_id(self, client, staff_token, customer_token):
        r = client.get('/api/v1/console/admin/customers/31', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200


# ---- inventory.py ----
class TestInventory:
    def test_get_parts(self, client, staff_token):
        r = client.get('/api/v1/console/admin/parts', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_low_stock(self, client, staff_token):
        r = client.get('/api/v1/console/admin/parts/low-stock', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200


# ---- backup_restore.py ----
class TestBackupRestore:
    def test_get_backup(self, client, staff_token):
        r = client.get('/api/v1/console/admin/backup', headers={'X-Staff-Token': staff_token})
        assert r.status_code in (200, 500)  # may fail if pg_dump unavailable


# ---- maintenance.py ----
class TestMaintenance:
    def test_get_reminders(self, client, staff_token):
        r = client.get('/api/v1/console/admin/maintenance-reminders', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_reminder_stats(self, client, staff_token):
        r = client.get('/api/v1/console/admin/maintenance-reminders/stats', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200
