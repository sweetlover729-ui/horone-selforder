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


# --- 以下由脚本追加 ---

# 1x1 pixel PNG in base64
_1X1_PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

class TestWorkflowPhotoSaving:
    """照片保存路径（valid base64，非 corrupt）"""

    def test_receive_new_format_photos(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/receive',
                       json={'express_company':'SF', 'express_no':'X1',
                             'photos': [{'type':'unbox','data':_1X1_PNG}]},
                       headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_receive_old_format_photos(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/receive',
                       json={'express_company':'SF', 'express_no':'X2',
                             'photos': [_1X1_PNG]},
                       headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_receive_no_express_company(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/receive',
                       json={}, headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)


class TestWorkflowReturnExpress:
    """回寄快递"""

    def test_update_return_express_success(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/return-express',
                       json={'return_express_no':'SF001'},
                       headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_update_return_express_empty(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/return-express',
                       json={}, headers=H(tech_token))
        data = json.loads(r.data)
        assert not data['success']
        _cl(db_conn, oid)


class TestWorkflowAcceptOrder:
    """接单端点"""

    def test_accept_order_success(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        r = client.post(f'/api/v1/console/tech/orders/{oid}/accept',
                        headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_accept_order_not_found(self, client, tech_token):
        r = client.post('/api/v1/console/tech/orders/99999/accept',
                        headers=H(tech_token))
        assert r.status_code == 404

    def test_accept_order_wrong_status(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'completed'); db_conn.commit()
        r = client.post(f'/api/v1/console/tech/orders/{oid}/accept',
                        headers=H(tech_token))
        assert r.status_code in (400, 404)
        _cl(db_conn, oid)

    def test_accept_order_already_assigned(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        # First assign to test tech
        client.post(f'/api/v1/console/tech/orders/{oid}/accept', headers=H(tech_token))
        # Second try - should return success (already yours)
        r = client.post(f'/api/v1/console/tech/orders/{oid}/accept',
                        headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)


class TestWorkflowSpecialServiceMore:
    """专项服务更多分支"""

    def test_create_empty_name_db_lookup(self, client, tech_token, db_conn):
        """name为空时从DB查"""
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing'); db_conn.commit()
        # Get a real special_service_id
        cur.execute("SELECT id FROM special_services LIMIT 1")
        svc = cur.fetchone()
        if svc:
            r = client.post(f'/api/v1/console/orders/{oid}/special-service',
                            json={'special_service_id': svc['id'], 'name': '',
                                  'price': 100, 'quantity': 1, 'photos': [],
                                  'staff_note': 'test'},
                            headers=H(tech_token))
            data = json.loads(r.data)
            assert data['success']
        _cl(db_conn, oid)

    def test_update_with_name_price_quantity(self, client, tech_token, db_conn):
        """更新 name+price+quantity"""
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing'); db_conn.commit()
        # Create first
        r = client.post(f'/api/v1/console/orders/{oid}/special-service',
                        json={'name':'TestBefore','price':50,'quantity':1,
                              'photos':[],'staff_note':'x'},
                        headers=H(tech_token))
        rec_id = json.loads(r.data).get('record_id')
        if rec_id:
            r2 = client.put(f'/api/v1/console/orders/{oid}/special-service/{rec_id}',
                            json={'name':'TestAfter','price':80,'quantity':2,
                                  'status':'confirmed'},
                            headers=H(tech_token))
            data2 = json.loads(r2.data)
            assert data2['success']
        _cl(db_conn, oid)


class TestWorkflowDeletePhoto:
    """删除照片 — 文件实际存在"""

    def test_delete_photo_old_format_string(self, client, tech_token, db_conn):
        """旧格式 string 路径删除"""
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        # Create a tracking node with old-format photo path string
        photo_rel = f"orders/{oid}/nodes/99989/test_del.jpg"
        fake_path = f"/Users/wjjmac/localserver/horone.selforder/backend/uploads/{photo_rel}"
        import os
        os.makedirs(os.path.dirname(fake_path), exist_ok=True)
        with open(fake_path, 'w') as f:
            f.write('x')
        cur.execute("""INSERT INTO tracking_nodes (id, order_id, node_code, node_name,
            operate_time, photos) VALUES (99989, %s, 'inspect', 'x', NOW(), %s)""",
            (oid, json.dumps([photo_rel])))
        db_conn.commit()
        r = client.delete(f'/api/v1/console/orders/{oid}/nodes/99989/photo/test_del.jpg',
                          headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        cur.execute("DELETE FROM tracking_nodes WHERE id=99989")
        db_conn.commit()
        _cl(db_conn, oid)

    def test_delete_photo_new_format_dict(self, client, tech_token, db_conn):
        """新格式 dict path 删除"""
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        photo_rel = f"orders/{oid}/nodes/99988/test_del2.jpg"
        fake_path = f"/Users/wjjmac/localserver/horone.selforder/backend/uploads/{photo_rel}"
        import os
        os.makedirs(os.path.dirname(fake_path), exist_ok=True)
        with open(fake_path, 'w') as f:
            f.write('x')
        cur.execute("""INSERT INTO tracking_nodes (id, order_id, node_code, node_name,
            operate_time, photos) VALUES (99988, %s, 'inspect', 'x', NOW(), %s)""",
            (oid, json.dumps([{'type':'unbox','path':photo_rel}])))
        db_conn.commit()
        r = client.delete(f'/api/v1/console/orders/{oid}/nodes/99988/photo/test_del2.jpg',
                          headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        cur.execute("DELETE FROM tracking_nodes WHERE id=99988")
        db_conn.commit()
        _cl(db_conn, oid)


class TestWorkflowEquipmentData:
    """设备检测数据端点"""

    def test_get_equipment_data(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'received'); db_conn.commit()
        r = client.get(f'/api/v1/console/orders/{oid}/equipment-data',
                       headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_save_equipment_with_valid_item(self, client, tech_token, db_conn):
        """插入正常检项"""
        cur = db_conn.cursor()
        oid = _mk(cur, 'received')
        # Create an order_item first
        cur.execute("SELECT id FROM product_types LIMIT 1")
        pt = cur.fetchone()
        pt_id = pt['id'] if pt else 1
        cur.execute("""INSERT INTO order_items (order_id, product_type_id, quantity)
            VALUES (%s, %s, 1) RETURNING id""", (oid, pt_id))
        oi_id = cur.fetchone()['id']
        db_conn.commit()
        r = client.post(f'/api/v1/console/orders/{oid}/equipment-data',
                        json={'items': [{
                            'order_item_id': oi_id,
                            'inspection_data': {
                                'first_stage_count': 2,
                                'first_stage_pre_pressure': ['130', '132'],
                                'first_stage_post_pressure': ['120', '122'],
                                'second_stage_count': 1,
                                'second_stage_pre_resistance': ['25'],
                                'second_stage_post_resistance': ['26']
                            }
                        }]},
                        headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)

    def test_save_equipment_update_existing(self, client, tech_token, db_conn):
        """更新已有检项"""
        cur = db_conn.cursor()
        oid = _mk(cur, 'received')
        cur.execute("SELECT id FROM product_types LIMIT 1")
        pt = cur.fetchone()
        pt_id = pt['id'] if pt else 1
        cur.execute("""INSERT INTO order_items (order_id, product_type_id, quantity)
            VALUES (%s, %s, 1) RETURNING id""", (oid, pt_id))
        oi_id = cur.fetchone()['id']
        # Pre-insert inspection data
        cur.execute("""INSERT INTO equipment_inspection_data
            (order_item_id, order_id, first_stage_count, second_stage_count, staff_id, staff_name)
            VALUES (%s, %s, 1, 1, 1, 'test')""", (oi_id, oid))
        db_conn.commit()
        # Now update
        r = client.put(f'/api/v1/console/orders/{oid}/equipment-data',
                       json={'items': [{
                           'order_item_id': oi_id,
                           'inspection_data': {
                               'first_stage_count': 3,
                               'first_stage_pre_pressure': ['140'],
                               'second_stage_count': 2,
                               'second_stage_pre_resistance': ['28']
                           }
                       }]},
                       headers=H(tech_token))
        data = json.loads(r.data)
        assert data['success']
        _cl(db_conn, oid)
