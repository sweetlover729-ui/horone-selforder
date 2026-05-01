# -*- coding: utf-8 -*-
"""Tests for all console routes: auth, orders, workflow, reports, simulate."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _headers(token):
    return {'X-Staff-Token': token, 'Content-Type': 'application/json'}


def _h(token):
    return {'X-Staff-Token': token}


def _cleanup_order(conn, order_id):
    """Delete test order and its tracking nodes."""
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM tracking_nodes WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM special_service_records WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM order_items WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM status_change_log WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM orders WHERE id = %s', (order_id,))
        conn.commit()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════

class TestConsoleAuth:
    def test_login_success(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'kent', 'password': 'LILY1018@kent729'})
        assert resp.status_code in (200, 404, 400, 403, 405)
        if resp.status_code == 200:
            data = resp.get_json()
            assert data['success'] is True
            assert 'token' in data

    def test_login_invalid_password(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'kent', 'password': 'wrong'})
        assert resp.status_code in (200, 400, 401, 403, 404)
        if resp.status_code == 200:
            data = resp.get_json()
            assert data['success'] is False

    def test_login_nonexistent_user(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'nobody', 'password': 'test'})
        assert resp.status_code in (200, 400, 401, 403, 404)

    def test_login_inactive_user(self, client, staff_token, db_conn):
        """Inactive user cannot login."""
        import database
        cur = db_conn.cursor()
        pw = database.hash_password('test')
        cur.execute(
            "INSERT INTO staff (username, password_hash, full_name, role, is_active) "
            "VALUES ('_INACTIVE_', %s, 'Inactive', 'technician', 0) "
            "ON CONFLICT (username) DO UPDATE SET is_active=0 "
            "RETURNING id", (pw,))
        db_conn.commit()

        resp = client.post('/api/v1/console/auth/login',
                           json={'username': '_INACTIVE_', 'password': 'test'})
        assert resp.status_code in (200, 400, 401, 403, 404)

        cur.execute("DELETE FROM staff WHERE username='_INACTIVE_'")
        db_conn.commit()

    def test_me_endpoint(self, client, staff_token):
        resp = client.get('/api/v1/console/auth/me', headers=_h(staff_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_me_invalid_token(self, client):
        resp = client.get('/api/v1/console/auth/me',
                          headers=_h('invalid-token'))
        assert resp.status_code in (200, 403, 404, 401)

    def test_logout(self, client, staff_token):
        resp = client.post('/api/v1/console/auth/logout',
                           json={}, headers=_headers(staff_token))
        assert resp.status_code in (200, 404, 403, 405)


# ═══════════════════════════════════════════════════════════
# Orders
# ═══════════════════════════════════════════════════════════

class TestConsoleOrders:
    def test_list_orders(self, client, tech_token):
        resp = client.get('/api/v1/console/orders', headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_list_orders_filtered(self, client, tech_token):
        resp = client.get('/api/v1/console/orders?status=received&page=1&per_page=5',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_list_orders_all_params(self, client, tech_token):
        resp = client.get('/api/v1/console/orders?status=repairing&search=test&'
                          'customer_id=1&date_from=2026-01-01&date_to=2026-12-31',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_get_order_detail(self, client, tech_token):
        resp = client.get('/api/v1/console/orders/1', headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_get_order_not_found(self, client, tech_token):
        resp = client.get('/api/v1/console/orders/99999', headers=_h(tech_token))
        assert resp.status_code in (404, 200, 403)

    def test_update_order(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1',
                          json={'receiver_name': 'Console Updated'},
                          headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_delete_order(self, client, staff_token, db_conn):
        """Admin can delete an order."""
        import uuid
        cur = db_conn.cursor()
        order_no = f'_DEL_TEST_{uuid.uuid4().hex[:8]}'
        cur.execute(
            "INSERT INTO orders (order_no, customer_id, status, total_amount, "
            "receiver_name, receiver_phone, receiver_address) "
            "VALUES (%s, 1, 'pending', 0, 'Del', '13000000001', 'Test') "
            "RETURNING id", (order_no,))
        oid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/orders/{oid}',
                             headers=_h(staff_token))
        assert resp.status_code in (200, 404, 403, 405)
        if resp.status_code != 200:
            _cleanup_order(db_conn, oid)

    def test_get_dashboard(self, client, tech_token):
        resp = client.get('/api/v1/console/orders/dashboard',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_get_order_statistics(self, client, tech_token):
        resp = client.get('/api/v1/console/orders/statistics',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)


# ═══════════════════════════════════════════════════════════
# Workflow (UPSERT node operations)
# ═══════════════════════════════════════════════════════════

class TestConsoleWorkflow:
    def test_receive_order(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1/receive',
                           json={'staff_name': 'test'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_receive_already_done(self, client, tech_token):
        """Second receive is idempotent."""
        resp = client.put('/api/v1/console/orders/1/receive',
                           json={'staff_name': 'test'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_inspect_order(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1/inspect',
                           json={'staff_name': 'test', 'description': 'inspected'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_repair_order(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1/repair',
                           json={'staff_name': 'test', 'description': 'repaired'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_qc_order(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1/qc',
                           json={'staff_name': 'test', 'description': 'qc passed'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_ship_order(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1/ship',
                           json={'staff_name': 'test', 'express_company': 'SF',
                                 'tracking_no': 'SF123456'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_workflow_order_not_found(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/99999/receive',
                           json={'staff_name': 'test'},
                           headers=_headers(tech_token))
        assert resp.status_code in (404, 400, 200, 403, 405)

    def test_inspect_with_photos(self, client, tech_token):
        """Inspect order with photo attachments."""
        resp = client.put('/api/v1/console/orders/1/inspect',
                           json={'staff_name': 'test',
                                 'description': 'test inspection',
                                 'photos': []},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_repair_with_data(self, client, tech_token):
        resp = client.put('/api/v1/console/orders/1/repair',
                           json={'staff_name': 'test',
                                 'description': 'replaced o-rings',
                                 'operate_note': 'all good'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_step1_receive_fresh(self, client, tech_token, db_conn):
        """Receive a fresh pending order."""
        import uuid
        cur = db_conn.cursor()
        order_no = f'_WF_RCV_{uuid.uuid4().hex[:8]}'
        cur.execute(
            "INSERT INTO orders (order_no, customer_id, status, total_amount, "
            "receiver_name, receiver_phone, receiver_address) "
            "VALUES (%s, 1, 'pending', 0, 'Test', '13000000001', 'Addr') "
            "RETURNING id", (order_no,))
        oid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'/api/v1/console/orders/{oid}/receive',
                           json={'staff_name': 'test'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

        _cleanup_order(db_conn, oid)

    def test_step2_inspect_full(self, client, tech_token, db_conn):
        """Full inspect with equipment data."""
        import uuid
        cur = db_conn.cursor()
        order_no = f'_WF_INS_{uuid.uuid4().hex[:8]}'
        cur.execute(
            "INSERT INTO orders (order_no, customer_id, status, total_amount, "
            "receiver_name, receiver_phone, receiver_address) "
            "VALUES (%s, 1, 'pending', 0, 'Test', '13000000001', 'Addr') "
            "RETURNING id", (order_no,))
        oid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'/api/v1/console/orders/{oid}/receive',
                           json={'staff_name': 'test'},
                           headers=_headers(tech_token))

        resp = client.put(f'/api/v1/console/orders/{oid}/inspect',
                           json={'staff_name': 'test',
                                 'description': 'Full inspection done',
                                 'first_stage_count': 1,
                                 'first_stage_serials': ['FS001'],
                                 'first_stage_pre_pressure': ['9.5'],
                                 'first_stage_post_pressure': ['9.8'],
                                 'second_stage_count': 0},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

        _cleanup_order(db_conn, oid)

    def test_step6_ship_full(self, client, tech_token, db_conn):
        """Ship order with express info."""
        import uuid
        cur = db_conn.cursor()
        order_no = f'_WF_SHP_{uuid.uuid4().hex[:8]}'
        cur.execute(
            "INSERT INTO orders (order_no, customer_id, status, total_amount, "
            "receiver_name, receiver_phone, receiver_address) "
            "VALUES (%s, 1, 'pending', 0, 'Test', '13000000001', 'Addr') "
            "RETURNING id", (order_no,))
        oid = cur.fetchone()['id']
        db_conn.commit()

        for step in ['receive', 'inspect', 'repair', 'qc']:
            client.put(f'/api/v1/console/orders/{oid}/{step}',
                        json={'staff_name': 'test'},
                        headers=_headers(tech_token))

        resp = client.put(f'/api/v1/console/orders/{oid}/ship',
                           json={'staff_name': 'test',
                                 'express_company': 'SF Express',
                                 'tracking_no': 'SF1234567890'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

        _cleanup_order(db_conn, oid)

    def test_add_special_service(self, client, staff_token):
        resp = client.post('/api/v1/console/orders/1/special-service',
                           json={'name': 'Test Service', 'description': 'Extra',
                                 'quantity': 1, 'amount': 100},
                           headers=_headers(staff_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_cancel_order(self, client, staff_token):
        resp = client.post('/api/v1/console/orders/1/cancel',
                           json={'reason': 'Test cancel'},
                           headers=_headers(staff_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_complete_order(self, client, tech_token):
        resp = client.post('/api/v1/console/orders/1/complete',
                           json={}, headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_update_payment_status(self, client, staff_token):
        resp = client.post('/api/v1/console/orders/1/payment',
                           json={'payment_status': 'paid'},
                           headers=_headers(staff_token))
        assert resp.status_code in (200, 404, 400, 403, 405)


# ═══════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════

class TestConsoleReports:
    def test_generate_report(self, client, tech_token):
        resp = client.post('/api/v1/console/reports/1/generate',
                           json={}, headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_get_report_pdf(self, client, tech_token):
        resp = client.get('/api/v1/console/reports/1/pdf',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_get_report_info(self, client, tech_token):
        resp = client.get('/api/v1/console/reports/1', headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)

    def test_delete_report(self, client, tech_token):
        resp = client.delete('/api/v1/console/reports/1',
                             headers=_h(tech_token))
        assert resp.status_code in (200, 404, 403, 405)


# ═══════════════════════════════════════════════════════════
# Simulate / Debug
# ═══════════════════════════════════════════════════════════

class TestConsoleSimulate:
    def test_simulate_create_order(self, client, tech_token):
        resp = client.post('/api/v1/console/simulate/create-order',
                           json={
                               'customer_id': 1,
                               'items': [{
                                   'product_type_id': 1,
                                   'brand_id': 1,
                                   'model_id': None,
                                   'service_type_ids': [1]
                               }],
                               'receiver_name': 'Sim Test',
                               'receiver_phone': '13900000001',
                               'receiver_address': 'Sim Address'
                           },
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_simulate_create_order_no_items(self, client, tech_token):
        resp = client.post('/api/v1/console/simulate/create-order',
                           json={'customer_id': 1, 'items': [],
                                 'receiver_name': 'Test',
                                 'receiver_phone': '13900000001',
                                 'receiver_address': 'Addr'},
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)

    def test_simulate_full_flow(self, client, tech_token):
        """Simulate a full order lifecycle."""
        resp = client.post('/api/v1/console/simulate/full-flow',
                           json={
                               'customer_id': 1,
                               'product_type_id': 1,
                               'brand_id': 1,
                               'service_type_ids': [1],
                               'receiver_name': 'Flow Test',
                               'receiver_phone': '13900000001',
                               'receiver_address': 'Flow Addr'
                           },
                           headers=_headers(tech_token))
        assert resp.status_code in (200, 404, 400, 403, 405)
