"""Smoke tests for routes_console/ endpoints"""
import pytest


class TestConsoleAuth:
    def test_login_admin(self, client):
        r = client.post('/api/v1/console/auth/login',
            json={'username': 'kent', 'password': 'LILY1018@kent729'})
        assert r.status_code in (200, 401)

    def test_login_technician(self, client):
        r = client.post('/api/v1/console/auth/login',
            json={'username': 'test', 'password': 'test123456'})
        assert r.status_code in (200, 401)

    def test_auth_me(self, client, staff_token):
        r = client.get('/api/v1/console/auth/me',
            headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_no_token_guest_access(self, client):
        r = client.get('/api/v1/console/auth/me')
        assert r.status_code in (200, 401, 403)


class TestConsoleOrders:
    def test_get_orders(self, client, staff_token):
        r = client.get('/api/v1/console/orders', headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_get_tech_orders(self, client, tech_token):
        r = client.get('/api/v1/console/tech/orders',
            headers={'X-Staff-Token': tech_token})
        assert r.status_code == 200


class TestConsoleDashboard:
    def test_dashboard_stats(self, client, staff_token):
        r = client.get('/api/v1/console/dashboard/stats',
            headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200

    def test_dashboard_report(self, client, staff_token):
        r = client.get('/api/v1/console/dashboard/report',
            headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200


class TestConsoleServiceItems:
    def test_get_service_items(self, client, staff_token):
        r = client.get('/api/v1/console/service-items?product_type_id=1',
            headers={'X-Staff-Token': staff_token})
        assert r.status_code == 200
