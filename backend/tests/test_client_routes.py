"""Smoke tests for routes_client/ endpoints"""
import pytest


class TestClientAuth:
    def test_phone_login(self, client):
        r = client.post('/api/v1/client/auth/phone-login', json={'phone': '13900000001', 'name': 'TestUser'})
        assert r.status_code == 200

    def test_phone_login_bad_phone(self, client):
        r = client.post('/api/v1/client/auth/phone-login', json={'phone': '12345', 'name': ''})
        assert r.status_code in (400, 422)

    def test_wechat_login_mock(self, client):
        r = client.post('/api/v1/client/auth/wechat-login', json={'code': 'test_code'})
        assert r.status_code in (200, 400)


class TestClientProducts:
    def test_get_product_types(self, client):
        r = client.get('/api/v1/client/products/types')
        assert r.status_code == 200

    def test_get_brands(self, client):
        r = client.get('/api/v1/client/products/brands')
        assert r.status_code == 200

    def test_get_categories(self, client):
        r = client.get('/api/v1/client/products/categories')
        assert r.status_code == 200

    def test_get_models(self, client):
        r = client.get('/api/v1/client/products/models')
        assert r.status_code == 200

    def test_get_full_products(self, client):
        r = client.get('/api/v1/client/products/full')
        assert r.status_code == 200


class TestClientServices:
    def test_get_services(self, client):
        r = client.get('/api/v1/client/services')
        assert r.status_code == 200

    def test_get_special_services(self, client):
        r = client.get('/api/v1/client/special-services')
        assert r.status_code == 200

    def test_get_price(self, client):
        r = client.get('/api/v1/client/price?product_type_id=1&service_type_id=15')
        assert r.status_code in (200, 400)

    def test_get_prices(self, client):
        r = client.get('/api/v1/client/prices?product_type_ids=1&service_type_id=15')
        assert r.status_code in (200, 400)


class TestClientOrders:
    def test_my_orders_no_auth(self, client):
        r = client.get('/api/v1/client/orders/my')
        assert r.status_code == 401

    def test_my_orders_with_token(self, client, customer_token):
        r = client.get('/api/v1/client/orders/my', headers={'Authorization': f'Bearer {customer_token}'})
        assert r.status_code == 200

    def test_create_order_minimal(self, client, customer_token):
        r = client.post('/api/v1/client/orders',
            json={'items': [{'product_type_id': 1, 'service_type_id': 15, 'quantity': 1}]},
            headers={'Authorization': f'Bearer {customer_token}'})
        assert r.status_code == 200

    def test_get_order(self, client, customer_token):
        orders_r = client.get('/api/v1/client/orders/my',
            headers={'Authorization': f'Bearer {customer_token}'})
        orders = orders_r.get_json()
        if orders.get('orders') and len(orders['orders']) > 0:
            oid = orders['orders'][0]['id']
            r = client.get(f'/api/v1/client/orders/{oid}',
                headers={'Authorization': f'Bearer {customer_token}'})
            assert r.status_code == 200

    def test_get_order_tracking(self, client, customer_token):
        orders_r = client.get('/api/v1/client/orders/my',
            headers={'Authorization': f'Bearer {customer_token}'})
        orders = orders_r.get_json()
        if orders.get('orders') and len(orders['orders']) > 0:
            oid = orders['orders'][0]['id']
            r = client.get(f'/api/v1/client/orders/{oid}/tracking',
                headers={'Authorization': f'Bearer {customer_token}'})
            assert r.status_code == 200


class TestClientReports:
    def test_overview(self, client, customer_token):
        r = client.get('/api/v1/client/reports/overview',
            headers={'Authorization': f'Bearer {customer_token}'})
        assert r.status_code == 200

    def test_recent(self, client, customer_token):
        r = client.get('/api/v1/client/reports/recent',
            headers={'Authorization': f'Bearer {customer_token}'})
        assert r.status_code == 200
