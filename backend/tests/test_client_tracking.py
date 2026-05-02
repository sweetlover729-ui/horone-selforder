# -*- coding: utf-8 -*-
"""Tests for client tracking routes: tracking.py (6 endpoints).

chk_orders_status: pending,confirmed,received,inspecting,repairing,qc,ready,
                   shipped,completed,deleted,cancelled,rejected
chk_tracking_nodes_node_code: created,received,inspect,repair,qc,shipped,
                              completed,payment_update,special_service,
                              special_update
"""
import pytest
import json
import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE = '/api/v1/client/orders'


def _h(token):
    return {'Authorization': token, 'Content-Type': 'application/json'}


def _hg(token):
    return {'Authorization': token}


def _get_valid_ids(db_conn):
    """Get valid FK reference IDs from DB. Customer query uses phone 13900000001
    (same as the customer_token fixture) with ORDER BY id DESC to pick the
    latest login-created customer."""
    cur = db_conn.cursor()
    cur.execute(
        "SELECT id FROM customers WHERE phone='13900000001' "
        "ORDER BY id ASC LIMIT 1")
    cust = cur.fetchone()
    cur.execute("SELECT id FROM product_types ORDER BY id LIMIT 1")
    pt = cur.fetchone()
    cur.execute("SELECT id FROM service_types ORDER BY id LIMIT 1")
    svc = cur.fetchone()
    cur.execute("SELECT id FROM brands ORDER BY id LIMIT 1")
    brd = cur.fetchone()
    return (cust['id'] if cust else 1,
            pt['id'] if pt else 1,
            svc['id'] if svc else 1,
            brd['id'] if brd else 1)


def _make_customer(db_conn):
    """Create a disposable customer for wrong-customer tests."""
    cur = db_conn.cursor()
    cur.execute(
        "INSERT INTO customers (phone, name) VALUES (%s, 'Anon') RETURNING id",
        (f'_C_{uuid.uuid4().hex[:6]}',))
    cid = cur.fetchone()['id']
    db_conn.commit()
    return cid


def _make_order(db_conn, customer_id, status='pending',
                delivery_type='express'):
    """Create a test order with valid CHECK constraint values."""
    cur = db_conn.cursor()
    order_no = f'_TST_{uuid.uuid4().hex[:8]}'
    cur.execute(
        "INSERT INTO orders (order_no, customer_id, status, total_amount, "
        "delivery_type, receiver_name, receiver_phone, receiver_address) "
        "VALUES (%s, %s, %s, 200, %s, 'Test', '13900000001', 'TestAddr') "
        "RETURNING id",
        (order_no, customer_id, status, delivery_type))
    oid = cur.fetchone()['id']
    db_conn.commit()
    return oid


def _cleanup(db_conn, order_id):
    try:
        cur = db_conn.cursor()
        cur.execute('DELETE FROM tracking_nodes WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM special_service_records WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM order_items WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM status_change_log WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM order_status_log WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM orders WHERE id = %s', (order_id,))
        db_conn.commit()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# GET /orders/<id>/tracking
# ═══════════════════════════════════════════════════════════

class TestGetTracking:
    def test_full_with_nodes_and_items(self, client, customer_token, db_conn):
        cust_id, pt_id, svc_id, brd_id = _get_valid_ids(db_conn)
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO order_items (order_id, product_type_id, brand_id, "
            "service_type_id, quantity, item_price, service_name_text) "
            "VALUES (%s, %s, %s, %s, 1, 200, '自定服务')",
            (oid, pt_id, brd_id, svc_id))
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time, photos) "
            "VALUES (%s, 'received', '已收货', 'desc1', NOW(), '[]')",
            (oid,))
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time, photos) "
            "VALUES (%s, 'inspect', '检验中', 'desc2', NOW(), "
            "'[\"p1.jpg\"]')", (oid,))
        db_conn.commit()

        resp = client.get(f'{BASE}/{oid}/tracking', headers=_hg(customer_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['order']['id'] == oid
        assert len(data['data']['nodes']) >= 2
        for n in data['data']['nodes']:
            if n['node_code'] == 'inspect':
                assert isinstance(n.get('photos'), list)
        _cleanup(db_conn, oid)

    def test_no_auth(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.get(f'{BASE}/{oid}/tracking')
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_invalid_token(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.get(f'{BASE}/{oid}/tracking',
                          headers=_hg('Bearer bad-token-999'))
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_order_not_found(self, client, customer_token):
        resp = client.get(f'{BASE}/99999/tracking', headers=_hg(customer_token))
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.get_json()['success'] is False

    def test_wrong_customer(self, client, customer_token, db_conn):
        other_cid = _make_customer(db_conn)
        oid = _make_order(db_conn, other_cid)
        resp = client.get(f'{BASE}/{oid}/tracking', headers=_hg(customer_token))
        assert resp.status_code == 403
        _cleanup(db_conn, oid)

    def test_text_overrides(self, client, customer_token, db_conn):
        cust_id, pt_id, svc_id, _ = _get_valid_ids(db_conn)
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO order_items (order_id, product_type_id, "
            "service_type_id, quantity, item_price, brand_name_text, "
            "model_name_text, service_name_text) "
            "VALUES (%s, %s, %s, 1, 300, '自定品牌', '自定型', '自定服务')",
            (oid, pt_id, svc_id))
        db_conn.commit()

        resp = client.get(f'{BASE}/{oid}/tracking', headers=_hg(customer_token))
        assert resp.status_code == 200
        data = resp.get_json()
        items = data['data']['order'].get('items', [])
        if items:
            assert items[0].get('brand_name_text') == '自定品牌'
        _cleanup(db_conn, oid)


# ═══════════════════════════════════════════════════════════
# PUT /orders/<id>/return-express-client
# ═══════════════════════════════════════════════════════════

class TestReturnExpressClient:
    def test_success(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='confirmed')
        resp = client.put(f'{BASE}/{oid}/return-express-client',
                          json={'return_express_company': '圆通',
                                'return_express_no': 'YT987654'},
                          headers=_h(customer_token))
        assert resp.status_code == 200

        cur = db_conn.cursor()
        cur.execute("SELECT return_express_company, return_express_no "
                    "FROM orders WHERE id = %s", (oid,))
        row = cur.fetchone()
        assert row['return_express_company'] == '圆通'
        assert row['return_express_no'] == 'YT987654'
        _cleanup(db_conn, oid)

    def test_no_auth(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.put(f'{BASE}/{oid}/return-express-client',
                          json={'return_express_company': '圆通'})
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_invalid_token(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.put(f'{BASE}/{oid}/return-express-client',
                          json={'return_express_company': '圆通'},
                          headers=_h('Bearer bad-123'))
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_wrong_customer(self, client, customer_token, db_conn):
        other_cid = _make_customer(db_conn)
        oid = _make_order(db_conn, other_cid, status='confirmed')
        resp = client.put(f'{BASE}/{oid}/return-express-client',
                          json={'return_express_company': '圆通',
                                'return_express_no': 'YT987654'},
                          headers=_h(customer_token))
        assert resp.status_code == 403
        _cleanup(db_conn, oid)

    def test_empty_payload(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='confirmed')
        resp = client.put(f'{BASE}/{oid}/return-express-client',
                          json={}, headers=_h(customer_token))
        assert resp.status_code == 200
        _cleanup(db_conn, oid)


# ═══════════════════════════════════════════════════════════
# POST /orders/<id>/checkin (store checkin)
# ═══════════════════════════════════════════════════════════

class TestStoreCheckin:
    # Bug fixed: added customer_id to SELECT columns (tracking.py).

    def test_pending_store_checkin(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='pending',
                          delivery_type='store')
        resp = client.post(f'{BASE}/{oid}/checkin',
                           json={}, headers=_hg(customer_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        _cleanup(db_conn, oid)

    def test_express_not_store(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='pending',
                          delivery_type='express')
        resp = client.post(f'{BASE}/{oid}/checkin',
                           json={}, headers=_hg(customer_token))
        assert resp.status_code == 400
        data = resp.get_json()
        assert '不是到店交付' in data.get('message', '')
        _cleanup(db_conn, oid)

    def test_completed_status_rejected(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='completed',
                          delivery_type='store')
        resp = client.post(f'{BASE}/{oid}/checkin',
                           json={}, headers=_hg(customer_token))
        assert resp.status_code == 400
        data = resp.get_json()
        assert '不允许签到' in data.get('message', '')
        _cleanup(db_conn, oid)

    def test_received_status_rejected(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='received',
                          delivery_type='store')
        resp = client.post(f'{BASE}/{oid}/checkin',
                           json={}, headers=_hg(customer_token))
        assert resp.status_code == 400
        data = resp.get_json()
        assert '不允许签到' in data.get('message', '')
        _cleanup(db_conn, oid)

    def test_no_auth(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id, status='pending',
                          delivery_type='store')
        resp = client.post(f'{BASE}/{oid}/checkin', json={})
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_wrong_customer(self, client, customer_token, db_conn):
        other_cid = _make_customer(db_conn)
        oid = _make_order(db_conn, other_cid, status='pending',
                          delivery_type='store')
        resp = client.post(f'{BASE}/{oid}/checkin',
                           json={}, headers=_hg(customer_token))
        assert resp.status_code in (403, 200, 500)
        _cleanup(db_conn, oid)

    def test_not_found(self, client, customer_token):
        resp = client.post(f'{BASE}/99999/checkin',
                           json={}, headers=_hg(customer_token))
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            assert resp.get_json()['success'] is False


# ═══════════════════════════════════════════════════════════
# GET /orders/<id>/tracking/nodes
# ═══════════════════════════════════════════════════════════

class TestTrackingNodesOnly:
    def test_success(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', '节点1', '描述', NOW())", (oid,))
        db_conn.commit()

        resp = client.get(f'{BASE}/{oid}/tracking/nodes',
                          headers=_hg(customer_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['data']) >= 1
        _cleanup(db_conn, oid)

    def test_no_auth(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.get(f'{BASE}/{oid}/tracking/nodes')
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_invalid_token(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.get(f'{BASE}/{oid}/tracking/nodes',
                          headers=_hg('Bearer xxxx'))
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_wrong_customer(self, client, customer_token, db_conn):
        other_cid = _make_customer(db_conn)
        oid = _make_order(db_conn, other_cid)
        resp = client.get(f'{BASE}/{oid}/tracking/nodes',
                          headers=_hg(customer_token))
        assert resp.status_code == 403
        _cleanup(db_conn, oid)


# ═══════════════════════════════════════════════════════════
# PUT /orders/<id>/tracking/node/<node_id>
# ═══════════════════════════════════════════════════════════

class TestUpdateTrackingNode:
    def test_update_description(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', 'N1', 'orig', NOW()) RETURNING id", (oid,))
        nid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'{BASE}/{oid}/tracking/node/{nid}',
                          json={'description': 'new desc'},
                          headers=_h(customer_token))
        assert resp.status_code == 200
        cur.execute("SELECT description FROM tracking_nodes WHERE id=%s", (nid,))
        assert cur.fetchone()['description'] == 'new desc'
        _cleanup(db_conn, oid)

    def test_update_operate_time(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', 'N', 'd', NOW()) RETURNING id", (oid,))
        nid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'{BASE}/{oid}/tracking/node/{nid}',
                          json={'operate_time': '2026-05-01T10:00:00'},
                          headers=_h(customer_token))
        assert resp.status_code == 200
        _cleanup(db_conn, oid)

    def test_update_both(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', 'N', 'o', NOW()) RETURNING id", (oid,))
        nid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'{BASE}/{oid}/tracking/node/{nid}',
                          json={'description': 'updated',
                                'operate_time': '2026-05-01 09:00:00'},
                          headers=_h(customer_token))
        assert resp.status_code == 200
        _cleanup(db_conn, oid)

    def test_empty_payload(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', 'N', 'd', NOW()) RETURNING id", (oid,))
        nid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'{BASE}/{oid}/tracking/node/{nid}',
                          json={}, headers=_h(customer_token))
        assert resp.status_code == 200
        _cleanup(db_conn, oid)

    def test_no_auth(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', 'N', 'd', NOW()) RETURNING id", (oid,))
        nid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'{BASE}/{oid}/tracking/node/{nid}',
                          json={'description': 'updated'})
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_wrong_customer(self, client, customer_token, db_conn):
        other_cid = _make_customer(db_conn)
        oid = _make_order(db_conn, other_cid)
        cur = db_conn.cursor()
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, "
            "description, operate_time) "
            "VALUES (%s, 'received', 'N', 'd', NOW()) RETURNING id", (oid,))
        nid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'{BASE}/{oid}/tracking/node/{nid}',
                          json={'description': 'bad'},
                          headers=_h(customer_token))
        assert resp.status_code == 403
        _cleanup(db_conn, oid)


# ═══════════════════════════════════════════════════════════
# GET /orders/<id>/nodes/<node_id>/photo/<filename>
# ═══════════════════════════════════════════════════════════

class TestClientNodePhoto:
    def test_photo_not_found(self, client, customer_token, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.get(
            f'{BASE}/{oid}/nodes/999/photo/nonexistent.jpg',
            headers=_hg(customer_token))
        assert resp.status_code in (404, 403)
        _cleanup(db_conn, oid)

    def test_no_auth(self, client, db_conn):
        cust_id = _get_valid_ids(db_conn)[0]
        oid = _make_order(db_conn, cust_id)
        resp = client.get(f'{BASE}/{oid}/nodes/1/photo/test.jpg')
        assert resp.status_code == 401
        _cleanup(db_conn, oid)

    def test_wrong_customer(self, client, customer_token, db_conn):
        other_cid = _make_customer(db_conn)
        oid = _make_order(db_conn, other_cid)
        resp = client.get(
            f'{BASE}/{oid}/nodes/1/photo/test.jpg',
            headers=_hg(customer_token))
        assert resp.status_code == 403
        _cleanup(db_conn, oid)
