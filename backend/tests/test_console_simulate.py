# -*- coding: utf-8 -*-
"""Tests for console simulate routes: simulate.py."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE = '/api/v1/console/simulate'


def _headers(token):
    return {'X-Staff-Token': token, 'Content-Type': 'application/json'}


def _h(token):
    return {'X-Staff-Token': token}


def _cleanup_sim(db_conn, order_id):
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


def _get_ids(db_conn):
    """Get valid FK IDs."""
    cur = db_conn.cursor()
    cur.execute("SELECT id FROM product_types ORDER BY id LIMIT 1")
    pt = cur.fetchone()
    cur.execute("SELECT id FROM service_types ORDER BY id LIMIT 1")
    svc = cur.fetchone()
    cur.execute("SELECT id FROM brands ORDER BY id LIMIT 1")
    brd = cur.fetchone()
    return (pt['id'] if pt else 1,
            svc['id'] if svc else 1,
            brd['id'] if brd else 1)


class TestSimulateCreate:
    def test_admin_create(self, client, staff_token, db_conn):
        resp = client.post(f'{BASE}/create',
                           json={},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['order_id'] > 0
        assert data['data']['order_no'].startswith('SIM-')
        _cleanup_sim(db_conn, data['data']['order_id'])

    def test_tech_create(self, client, tech_token):
        resp = client.post(f'{BASE}/create', json={}, headers=_headers(tech_token))
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_no_auth(self, client):
        resp = client.post(f'{BASE}/create', json={})
        assert resp.status_code in (403, 401)

    def test_multiple_unique(self, client, staff_token, db_conn):
        ids = []
        for _ in range(2):
            resp = client.post(f'{BASE}/create', json={},
                               headers=_headers(staff_token))
            assert resp.status_code == 200
            ids.append(resp.get_json()['data']['order_id'])
        assert ids[0] != ids[1]
        for oid in ids:
            _cleanup_sim(db_conn, oid)


class TestSimulateStep:
    def _create_sim(self, client, token):
        resp = client.post(f'{BASE}/create', json={}, headers=_headers(token))
        return resp.get_json()['data']

    def test_step_pay_express(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']
        pt_id, svc_id, brd_id = _get_ids(db_conn)

        resp = client.post(f'{BASE}/{oid}/step/pay',
                           json={
                               'delivery_type': 'express',
                               'service_type_id': svc_id,
                               'product_type_id': pt_id,
                               'brand_id': brd_id,
                           },
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

        cur = db_conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM order_items WHERE order_id = %s", (oid,))
        assert cur.fetchone()['cnt'] >= 1
        _cleanup_sim(db_conn, oid)

    def test_step_pay_store(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']
        pt_id, svc_id, brd_id = _get_ids(db_conn)

        resp = client.post(f'{BASE}/{oid}/step/pay',
                           json={'delivery_type': 'store',
                                 'service_type_id': svc_id,
                                 'product_type_id': pt_id,
                                 'brand_id': brd_id},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        cur = db_conn.cursor()
        cur.execute("SELECT delivery_type FROM orders WHERE id = %s", (oid,))
        assert cur.fetchone()['delivery_type'] == 'store'
        _cleanup_sim(db_conn, oid)

    def test_step_receive(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/receive',
                           json={'express_company': '顺丰',
                                 'express_no': 'SF123456',
                                 'note': '包裹完好'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        _cleanup_sim(db_conn, oid)

    def test_step_receive_with_photo(self, client, staff_token, db_conn):
        """Receive with tiny JPEG base64 photo."""
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']
        tiny_jpg = (
            '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkS'
            'Ew8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAARCAAB'
            'AAEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QA'
            'AtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRV'
            'S0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZn'
            'aGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDx'
            'MXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQ'
            'EBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx'
            'BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYIzhCJygpKjFhg4Sk5'
            'PUlNMTU5VldYWVpkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp'
            '6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn'
            '6/9oADAMBAAIRAxEAPwD3+iiigD//2Q==')
        resp = client.post(f'{BASE}/{oid}/step/receive',
                           json={'photos': [f'data:image/jpeg;base64,{tiny_jpg}'],
                                 'note': '拆包检查'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        _cleanup_sim(db_conn, oid)

    def test_step_inspect(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/inspect',
                           json={'note': '设备正常'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        _cleanup_sim(db_conn, oid)

    def test_step_repair(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/repair',
                           json={'note': '已保养'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        _cleanup_sim(db_conn, oid)

    def test_step_qc(self, client, staff_token, db_conn):
        """QC generates PDF."""
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']
        pt_id, svc_id, brd_id = _get_ids(db_conn)

        client.post(f'{BASE}/{oid}/step/pay',
                    json={'delivery_type': 'store',
                          'service_type_id': svc_id,
                          'product_type_id': pt_id,
                          'brand_id': brd_id},
                    headers=_headers(staff_token))

        resp = client.post(f'{BASE}/{oid}/step/qc',
                           json={'note': '合格'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        _cleanup_sim(db_conn, oid)

    def test_step_ship(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/ship',
                           json={'return_express_company': '圆通',
                                 'return_express_no': 'YT123456',
                                 'note': '已发出'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200

        cur = db_conn.cursor()
        cur.execute("SELECT return_express_company FROM orders WHERE id = %s", (oid,))
        assert cur.fetchone()['return_express_company'] == '圆通'
        _cleanup_sim(db_conn, oid)

    def test_step_complete(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/complete',
                           json={'note': '签收完成'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200

        cur = db_conn.cursor()
        cur.execute("SELECT status, completed_at FROM orders WHERE id = %s", (oid,))
        row = cur.fetchone()
        assert row['status'] == 'completed'
        assert row['completed_at'] is not None
        _cleanup_sim(db_conn, oid)

    def test_step_unknown(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/nonexistent',
                           json={}, headers=_headers(staff_token))
        assert resp.status_code == 400
        _cleanup_sim(db_conn, oid)

    def test_step_fake_order(self, client, staff_token):
        resp = client.post(f'{BASE}/99999/step/receive',
                           json={}, headers=_headers(staff_token))
        assert resp.status_code == 404

    def test_step_no_auth(self, client):
        resp = client.post(f'{BASE}/1/step/receive', json={})
        assert resp.status_code in (401, 403)

    def test_tech_execute_steps(self, client, tech_token, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']

        resp = client.post(f'{BASE}/{oid}/step/inspect',
                           json={'note': 'tech did this'},
                           headers=_headers(tech_token))
        assert resp.status_code == 200
        _cleanup_sim(db_conn, oid)

    def test_full_lifecycle(self, client, staff_token, db_conn):
        sim = self._create_sim(client, staff_token)
        oid = sim['order_id']
        pt_id, svc_id, brd_id = _get_ids(db_conn)

        steps = [
            ('pay',    {'delivery_type': 'store',
                        'service_type_id': svc_id,
                        'product_type_id': pt_id, 'brand_id': brd_id}),
            ('receive', {'note': 'Received'}),
            ('inspect', {'note': 'Inspected'}),
            ('repair',  {'note': 'Repaired'}),
            ('qc',      {'note': 'QC OK'}),
            ('ship',    {'note': 'Shipped'}),
            ('complete', {'note': 'Done'}),
        ]
        for step, payload in steps:
            resp = client.post(f'{BASE}/{oid}/step/{step}',
                               json=payload, headers=_headers(staff_token))
            assert resp.status_code == 200, f'Step {step} failed: {resp.get_json()}'
            assert resp.get_json()['success'] is True

        cur = db_conn.cursor()
        cur.execute("SELECT status FROM orders WHERE id = %s", (oid,))
        assert cur.fetchone()['status'] == 'completed'

        cur.execute("SELECT COUNT(*) as cnt FROM tracking_nodes WHERE order_id = %s", (oid,))
        assert cur.fetchone()['cnt'] >= 7

        _cleanup_sim(db_conn, oid)


class TestSimulateCleanup:
    def test_cleanup_empty(self, client, staff_token):
        resp = client.post(f'{BASE}/cleanup', json={},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        # May also contain leftover sim orders from prior failed runs
        assert '模拟订单' in data.get('message', '') or '已清理' in data.get('message', '')

    def test_cleanup_with_orders(self, client, staff_token, db_conn):
        ids = []
        for _ in range(2):
            resp = client.post(f'{BASE}/create', json={},
                               headers=_headers(staff_token))
            ids.append(resp.get_json()['data']['order_id'])

        resp = client.post(f'{BASE}/cleanup', json={},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert '已清理' in data.get('message', '')

        cur = db_conn.cursor()
        for oid in ids:
            cur.execute(
                "SELECT COUNT(*) as cnt FROM orders WHERE id = %s AND is_simulation = 1",
                (oid,))
            assert cur.fetchone()['cnt'] == 0

    def test_cleanup_tech_forbidden(self, client, tech_token):
        resp = client.post(f'{BASE}/cleanup', json={},
                           headers=_headers(tech_token))
        assert resp.status_code == 403

    def test_cleanup_no_auth(self, client):
        resp = client.post(f'{BASE}/cleanup', json={})
        assert resp.status_code in (403, 401)