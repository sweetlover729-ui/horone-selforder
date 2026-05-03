# -*- coding: utf-8 -*-
"""Workflow gap coverage supplementary tests."""
import pytest
import json
import uuid
from unittest.mock import patch

H = lambda t: {'X-Staff-Token': t}

def _mk(cur, status='pending'):
    oid = f'GAP_{uuid.uuid4().hex[:8]}'
    cur.execute(
        "INSERT INTO orders (order_no, customer_id, status, total_amount, "
        "receiver_name, receiver_phone, receiver_address) "
        "VALUES (%s, 1, %s, 0, 'T', '13000000001', 'A') RETURNING id",
        (oid, status))
    return cur.fetchone()['id']

def _cl(conn, oid):
    cur = conn.cursor()
    for t in ['special_service_records','tracking_nodes','equipment_inspection_data',
              'order_status_log','status_change_log','order_items','orders']:
        try: cur.execute(f'DELETE FROM {t} WHERE order_id=%s', (oid,))
        except: pass
    conn.commit()


class TestWorkflowJsonLoadsExceptions:
    """json.loads 异常分支 — 预置非法 JSON"""

    def test_receive_corrupt_photos(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'pending'); db_conn.commit()
        # 预置一个 tracking_node 含非法 JSON photos
        cur.execute("""INSERT INTO tracking_nodes (order_id, node_code, node_name,
            operate_time, photos) VALUES (%s, 'received', 'x', NOW(), 'NOT!!JSON!!')""", (oid,))
        db_conn.commit()

        r = client.put(f'/api/v1/console/orders/{oid}/receive',
                       json={'express_company':'SF'}, headers=H(tech_token))
        assert r.status_code == 200
        _cl(db_conn, oid)

    def test_inspect_corrupt_photos(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        cur.execute("""INSERT INTO tracking_nodes (order_id, node_code, node_name,
            operate_time, photos) VALUES (%s, 'inspect', 'x', NOW(), '{broken')""", (oid,))
        db_conn.commit()

        r = client.put(f'/api/v1/console/orders/{oid}/inspect',
                       json={'photos':[]}, headers=H(tech_token))
        assert r.status_code == 200
        _cl(db_conn, oid)

    def test_qc_corrupt_photos(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing'); db_conn.commit()
        cur.execute("""INSERT INTO tracking_nodes (order_id, node_code, node_name,
            operate_time, photos) VALUES (%s, 'qc', 'x', NOW(), 'bad json')""", (oid,))
        db_conn.commit()

        with patch('routes_console.workflow._integration_hook_notify'):
            r = client.put(f'/api/v1/console/orders/{oid}/qc',
                           json={'photos':[]}, headers=H(tech_token))
            assert r.status_code == 200
        _cl(db_conn, oid)

    def test_ship_corrupt_photos(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'ready'); db_conn.commit()
        cur.execute("""INSERT INTO tracking_nodes (order_id, node_code, node_name,
            operate_time, photos) VALUES (%s, 'shipped', 'x', NOW(), '}{')""", (oid,))
        db_conn.commit()

        r = client.put(f'/api/v1/console/orders/{oid}/ship',
                       json={'return_express_no':'SF1','photos':[]}, headers=H(tech_token))
        assert r.status_code == 200
        _cl(db_conn, oid)


class TestWorkflowStatusGuards:
    """状态卫士分支"""

    def test_inspect_rejects_confirmed(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/inspect',
                       json={'photos':[]}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']
        _cl(db_conn, oid)

    def test_repair_rejects_confirmed(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/repair',
                       json={'photos':[],'selected_items':[]}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']
        _cl(db_conn, oid)

    def test_qc_rejects_received(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/qc',
                       json={'photos':[]}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']
        _cl(db_conn, oid)

    def test_ship_rejects_received(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/ship',
                       json={'return_express_no':'xx','photos':[]}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']
        _cl(db_conn, oid)

    def test_complete_rejects_received(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/complete',
                       json={}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']
        _cl(db_conn, oid)


class TestWorkflowEdgeCases:
    """其他边缘路径"""

    def test_complete_order_not_found(self, client, tech_token):
        r = client.put('/api/v1/console/orders/99999/complete',
                       json={}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success'] or r.status_code != 200

    def test_qc_order_not_found(self, client, tech_token):
        with patch('routes_console.workflow._integration_hook_notify'):
            r = client.put('/api/v1/console/orders/99999/qc',
                           json={'photos':[]}, headers=H(tech_token))
            data = json.loads(r.data)
            assert not data['success']

    def test_ship_order_not_found(self, client, tech_token):
        r = client.put('/api/v1/console/orders/99999/ship',
                       json={'return_express_no':'x','photos':[]}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']

    def test_complete_already_completed_branch(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'completed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/complete',
                       json={}, headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_delete_photo_not_in_node(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        cur.execute("""INSERT INTO tracking_nodes (id, order_id, node_code, node_name,
            operate_time, photos) VALUES (99990, %s, 'received', 'x', NOW(), '[]')""", (oid,))
        db_conn.commit()
        r = client.delete(f'/api/v1/console/orders/{oid}/nodes/99990/photo/fake.jpg',
                          headers=H(tech_token))
        assert r.status_code == 404
        cur.execute("DELETE FROM tracking_nodes WHERE id=99990")
        db_conn.commit()
        _cl(db_conn, oid)

    def test_save_equipment_no_items(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        r = client.post(f'/api/v1/console/orders/{oid}/equipment-data',
                        json={'items':[]}, headers=H(tech_token))
        assert r.status_code == 400
        data = json.loads(r.data)
        assert not data['success']
        assert '无数据' in data.get('message', '')
        _cl(db_conn, oid)
