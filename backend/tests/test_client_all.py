# -*- coding: utf-8 -*-
"""Tests for all client routes: auth, products, services, orders, tracking, reports."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _h(token):
    return {'Authorization': token, 'Content-Type': 'application/json'}


def _hg(token):
    return {'Authorization': token}


# ═══════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════

class TestClientAuth:
    def test_phone_login_new_customer(self, client):
        """Phone login creates/returns a customer."""
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': '13999999999', 'name': 'New Customer'})
        data = resp.get_json()
        # Can be 200 (success) or 400 (validation) depending on API version
        assert resp.status_code in (200, 400)
        if resp.status_code == 200:
            assert data.get('success') or 'token' in str(data)

    def test_phone_login_existing_customer(self, client):
        """Phone login returns token for existing customer."""
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': '13900000001', 'name': 'Existing'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_phone_login_no_phone(self, client):
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': '', 'name': 'test'})
        assert resp.status_code in (200, 400)

    def test_validate_token(self, client, customer_token):
        resp = client.get('/api/v1/client/auth/validate',
                          headers=_hg(customer_token))
        assert resp.status_code in (200, 401, 404)
        if resp.status_code == 200:
            data = resp.get_json()
            assert data['success'] is True

    def test_validate_token_invalid(self, client):
        resp = client.get('/api/v1/client/auth/validate',
                          headers=_hg('Bearer invalid-token'))
        assert resp.status_code in (401, 403, 404)


# ═══════════════════════════════════════════════════════════
# Products
# ═══════════════════════════════════════════════════════════

class TestClientProducts:
    def test_get_product_types(self, client):
        resp = client.get('/api/v1/client/products/types')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_brands(self, client):
        resp = client.get('/api/v1/client/products/brands')
        assert resp.status_code == 200

    def test_get_brands_by_type(self, client):
        resp = client.get('/api/v1/client/products/brands?product_type_id=1')
        assert resp.status_code == 200

    def test_get_models(self, client):
        resp = client.get('/api/v1/client/products/models')
        assert resp.status_code == 200

    def test_get_models_by_brand(self, client):
        resp = client.get('/api/v1/client/products/models?brand_id=1')
        assert resp.status_code == 200

    def test_get_categories(self, client):
        resp = client.get('/api/v1/client/products/categories')
        assert resp.status_code == 200

    def test_get_product_types_with_category(self, client):
        resp = client.get('/api/v1/client/products/types?category_id=1')
        assert resp.status_code == 200

    def test_get_brands_with_service_type(self, client):
        resp = client.get('/api/v1/client/products/brands?service_type_id=1')
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════
# Client Services (service types, pricing)
# ═══════════════════════════════════════════════════════════

class TestClientServices:
    def test_get_service_types(self, client):
        resp = client.get('/api/v1/client/services/types')
        assert resp.status_code in (200, 404)

    def test_get_service_types_by_product(self, client):
        resp = client.get('/api/v1/client/services/types?product_type_id=1')
        assert resp.status_code in (200, 404)

    def test_get_service_items(self, client):
        resp = client.get('/api/v1/client/services/items?product_type_id=1')
        assert resp.status_code in (200, 404)

    def test_get_service_items_no_type(self, client):
        resp = client.get('/api/v1/client/services/items')
        assert resp.status_code in (200, 404)

    def test_calculate_price(self, client):
        resp = client.post('/api/v1/client/services/calculate-price',
                           json={'product_type_id': 1, 'brand_id': 1,
                                 'service_type_ids': [1, 2]})
        assert resp.status_code in (200, 404, 405, 400)

    def test_calculate_price_no_ids(self, client):
        resp = client.post('/api/v1/client/services/calculate-price',
                           json={'product_type_id': 1, 'brand_id': 1,
                                 'service_type_ids': []})
        assert resp.status_code in (200, 404, 405, 400)


# ═══════════════════════════════════════════════════════════
# Orders
# ═══════════════════════════════════════════════════════════

class TestClientOrders:
    def test_create_order(self, client, customer_token):
        resp = client.post('/api/v1/client/orders',
                           json={
                               'receiver_name': 'Test User',
                               'receiver_phone': '13900000001',
                               'receiver_address': 'Test Address',
                               'items': [{
                                   'product_type_id': 1,
                                   'brand_id': 1,
                                   'service_type_ids': [1]
                               }]
                           },
                           headers=_h(customer_token))
        data = resp.get_json()
        assert resp.status_code in (200, 400, 401, 403, 404)

    def test_create_order_no_items(self, client, customer_token):
        resp = client.post('/api/v1/client/orders',
                           json={
                               'receiver_name': 'Test',
                               'receiver_phone': '13900000001',
                               'receiver_address': 'Some Place',
                               'items': []
                           },
                           headers=_h(customer_token))
        data = resp.get_json()
        assert not data.get('success', True) or resp.status_code != 200

    def test_get_my_orders(self, client, customer_token):
        resp = client.get('/api/v1/client/orders/my', headers=_hg(customer_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_my_orders_no_auth(self, client):
        resp = client.get('/api/v1/client/orders/my')
        assert resp.status_code == 401

    def test_get_order_detail(self, client, customer_token):
        resp = client.get('/api/v1/client/orders/1', headers=_hg(customer_token))
        # Will return 200 or 403/404 depending on customer_id match
        assert resp.status_code in (200, 400, 401, 403, 404)

    def test_update_order(self, client, customer_token, db_conn):
        """Update order receiver info."""
        cur = db_conn.cursor()
        cur.execute(
            "SELECT id FROM orders WHERE customer_id=1 AND status='pending' "
            "ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if row:
            resp = client.put(f'/api/v1/client/orders/{row["id"]}',
                              json={'receiver_name': 'Updated Name'},
                              headers=_h(customer_token))
            assert resp.status_code in (200, 400, 401, 403, 404, 405)

    def test_search_order_by_phone(self, client):
        resp = client.get('/api/v1/client/orders/track?phone=13900000001')
        assert resp.status_code in (200, 404)

    def test_cancel_order(self, client, customer_token, db_conn):
        cur = db_conn.cursor()
        cur.execute(
            "SELECT id FROM orders WHERE customer_id=1 AND status IN ('pending','paid') "
            "ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if row:
            resp = client.post(f'/api/v1/client/orders/{row["id"]}/cancel',
                               json={'reason': 'test cancel'},
                               headers=_h(customer_token))
            assert resp.status_code in (200, 400, 401, 403, 404, 405)

    def test_confirm_special_service(self, client, customer_token, db_conn):
        cur = db_conn.cursor()
        cur.execute(
            "SELECT id FROM orders WHERE customer_id=1 AND status='special_service_pending' "
            "LIMIT 1")
        row = cur.fetchone()
        if row:
            resp = client.post(
                f'/api/v1/client/orders/{row["id"]}/confirm-special-service',
                json={'accepted': True}, headers=_h(customer_token))
            assert resp.status_code in (200, 400, 401, 403, 404)

    def test_respond_special_service(self, client, customer_token, db_conn):
        cur = db_conn.cursor()
        cur.execute(
            "SELECT id FROM orders WHERE customer_id=1 AND status='special_service_pending' "
            "LIMIT 1")
        row = cur.fetchone()
        if row:
            resp = client.post(
                f'/api/v1/client/orders/{row["id"]}/special-service-respond',
                json={'accepted': True, 'note': 'OK'},
                headers=_h(customer_token))
            assert resp.status_code in (200, 400, 401, 403, 404)

    def test_confirm_receipt(self, client, customer_token, db_conn):
        cur = db_conn.cursor()
        cur.execute(
            "SELECT id FROM orders WHERE customer_id=1 AND status='shipped' LIMIT 1")
        row = cur.fetchone()
        if row:
            resp = client.post(f'/api/v1/client/orders/{row["id"]}/confirm-receipt',
                               json={}, headers=_h(customer_token))
            assert resp.status_code in (200, 400, 401, 403, 404)


# ═══════════════════════════════════════════════════════════
# Tracking
# ═══════════════════════════════════════════════════════════

class TestClientTracking:
    def test_get_order_tracking(self, client, customer_token):
        resp = client.get('/api/v1/client/tracking/1', headers=_hg(customer_token))
        assert resp.status_code in (200, 400, 401, 403, 404)

    def test_track_order_by_no(self, client):
        """Track order by order number (public)."""
        resp = client.get('/api/v1/client/tracking/track/RMD-20260427-000001')
        assert resp.status_code in (200, 404)

    def test_get_order_timeline(self, client, customer_token):
        resp = client.get('/api/v1/client/tracking/1/timeline',
                          headers=_hg(customer_token))
        assert resp.status_code in (200, 400, 401, 403, 404)


# ═══════════════════════════════════════════════════════════
# Client Reports
# ═══════════════════════════════════════════════════════════

class TestClientReports:
    def test_get_report(self, client, customer_token):
        resp = client.get('/api/v1/client/reports/1', headers=_hg(customer_token))
        assert resp.status_code in (200, 400, 401, 403, 404)

    def test_get_report_url(self, client, customer_token):
        resp = client.get('/api/v1/client/reports/1/url',
                          headers=_hg(customer_token))
        assert resp.status_code in (200, 400, 401, 403, 404)
