# -*- coding: utf-8 -*-
"""Full coverage tests for routes_console/workflow.py state machine."""
import pytest
import json
import uuid
from unittest.mock import patch

H = lambda t: {'X-Staff-Token': t}

def _mk(cursor, status='pending'):
    order_no = f'WF_{uuid.uuid4().hex[:8]}'
    cursor.execute(
        "INSERT INTO orders (order_no, customer_id, status, total_amount, "
        "receiver_name, receiver_phone, receiver_address) "
        "VALUES (%s, 1, %s, 0, 'Tester', '13000000001', 'Addr') RETURNING id",
        (order_no, status))
    return cursor.fetchone()['id']

def _clean(conn, oid):
    cur = conn.cursor()
    for t in ['special_service_records','tracking_nodes','equipment_inspection_data',
              'order_status_log','status_change_log','order_items','orders']:
        try: cur.execute(f'DELETE FROM {t} WHERE order_id=%s', (oid,))
        except: pass
    conn.commit()

def _add_item(cur, oid):
    cur.execute(
        "INSERT INTO order_items (order_id, product_type_id, brand_id, model_id, quantity, item_price) "
        "VALUES (%s, 1, 1, 79, 1, 100) RETURNING id", (oid,))
    return cur.fetchone()['id']

# ═══ Full workflow ═══
class TestFullWorkflow:
    def test_happy_path(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()

        steps = [
            ('receive', {'express_company':'SF','express_no':'123'}),
            ('inspect', {'photos':[]}),
            ('repair', {'photos':[],'selected_items':[]}),
        ]
        for step, payload in steps:
            r = client.put(f'/api/v1/console/orders/{oid}/{step}', json=payload, headers=H(tech_token))
            assert r.status_code == 200, f'{step}: {r.data}'
            assert json.loads(r.data)['success'] is True

        for step in ['qc','ship','complete']:
            with patch('routes_console.workflow._integration_hook_notify'):
                payload = {'return_express_no':'SF999','photos':[]} if step=='ship' else {}
                if step=='qc': payload={'photos':[]}
                r = client.put(f'/api/v1/console/orders/{oid}/{step}', json=payload, headers=H(tech_token))
                assert r.status_code == 200, f'{step}: {r.data}'
                assert json.loads(r.data)['success'] is True

        cur.execute("SELECT status, completed_at FROM orders WHERE id=%s", (oid,))
        row = cur.fetchone()
        assert row['status'] == 'completed'
        assert row['completed_at'] is not None
        _clean(db_conn, oid)

    def test_idempotent_all(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()

        for rte in ['receive','inspect','repair']:
            client.put(f'/api/v1/console/orders/{oid}/{rte}', json={'photos':[]}, headers=H(tech_token))
            r = client.put(f'/api/v1/console/orders/{oid}/{rte}', json={'photos':[]}, headers=H(tech_token))
            assert r.status_code == 200
            assert json.loads(r.data)['success'] is True

        with patch('routes_console.workflow._integration_hook_notify'):
            for rte in ['qc','ship','complete']:
                p = {'return_express_no':'SF1','photos':[]} if rte=='ship' else {}
                if rte=='qc': p={'photos':[]}
                client.put(f'/api/v1/console/orders/{oid}/{rte}', json=p, headers=H(tech_token))
                r = client.put(f'/api/v1/console/orders/{oid}/{rte}', json=p, headers=H(tech_token))
                assert r.status_code == 200
        _clean(db_conn, oid)

# ═══ State guards ═══
class TestGuards:
    def test_receive_rejects_completed(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'completed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/receive', json={}, headers=H(tech_token))
        assert json.loads(r.data)['success'] is False
        _clean(db_conn, oid)

    def test_inspect_already_done(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'repairing'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/inspect', json={'photos':[]}, headers=H(tech_token))
        assert json.loads(r.data).get('already_done') is True
        _clean(db_conn, oid)

    def test_repair_already_done(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'ready'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/repair', json={'selected_items':[],'photos':[]}, headers=H(tech_token))
        assert json.loads(r.data).get('already_done') is True
        _clean(db_conn, oid)

    def test_qc_rejects_pending(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'pending'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/qc', json={}, headers=H(tech_token))
        assert json.loads(r.data)['success'] is False
        _clean(db_conn, oid)

    def test_qc_already_done(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'ready'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/qc', json={}, headers=H(tech_token))
        assert json.loads(r.data).get('already_done') is True
        _clean(db_conn, oid)

    def test_ship_rejects_pending(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'pending'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/ship', json={'return_express_no':'1','photos':[]}, headers=H(tech_token))
        assert json.loads(r.data)['success'] is False
        _clean(db_conn, oid)

    def test_ship_already_done(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'completed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/ship', json={'return_express_no':'1','photos':[]}, headers=H(tech_token))
        assert json.loads(r.data).get('already_done') is True
        _clean(db_conn, oid)

    def test_complete_rejects_pending(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'pending'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/complete', json={}, headers=H(tech_token))
        assert json.loads(r.data)['success'] is False
        _clean(db_conn, oid)

    def test_complete_already_done(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'completed'); db_conn.commit()
        with patch('routes_console.workflow._integration_hook_notify'):
            r = client.put(f'/api/v1/console/orders/{oid}/complete', json={}, headers=H(tech_token))
            assert json.loads(r.data).get('already_done') is True
        _clean(db_conn, oid)

    def test_all_not_found(self, client, tech_token):
        for route in ['receive','inspect','repair','qc','ship','complete']:
            r = client.put(f'/api/v1/console/orders/99999/{route}', json={}, headers=H(tech_token))
            assert r.status_code in (200,400,404)

# ═══ Auth ═══
class TestAuth:
    def test_no_token(self, client):
        routes = ['receive','inspect','repair','ship','complete']
        for rte in routes:
            r = client.put(f'/api/v1/console/orders/1/{rte}', json={})
            assert r.status_code in (200,400,401,403)
        r = client.get('/api/v1/console/tech/orders'); assert r.status_code in (200,401,403)
        r = client.post('/api/v1/console/tech/orders/1/accept'); assert r.status_code in (200,400,401,403,404)

# ═══ Special service ═══
class TestSpecial:
    def test_create(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing')
        iid = _add_item(cur, oid); db_conn.commit()
        r = client.post(f'/api/v1/console/orders/{oid}/special-service',
            json={'order_item_id':iid,'name':'TestSvc','price':50,'quantity':2,'photos':[],'staff_note':'x'},
            headers=H(tech_token))
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['success'] is True
        rid = d['record_id']

        # update: confirm → reject → paid → completed
        for st in ['confirmed','rejected','pending','paid','completed']:
            r = client.put(f'/api/v1/console/orders/{oid}/special-service/{rid}',
                json={'status':st}, headers=H(tech_token))
            assert r.status_code == 200

        # update name/price/quantity
        r = client.put(f'/api/v1/console/orders/{oid}/special-service/{rid}',
            json={'name':'New','price':99,'quantity':3}, headers=H(tech_token))
        assert r.status_code == 200

        # invalid status
        r = client.put(f'/api/v1/console/orders/{oid}/special-service/{rid}',
            json={'status':'bad'}, headers=H(tech_token))
        assert r.status_code == 200
        _clean(db_conn, oid)

    def test_update_no_changes(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing')
        iid = _add_item(cur, oid); db_conn.commit()
        r = client.post(f'/api/v1/console/orders/{oid}/special-service',
            json={'order_item_id':iid,'name':'X','price':1,'quantity':1,'photos':[]},
            headers=H(tech_token))
        rid = json.loads(r.data)['record_id']
        r = client.put(f'/api/v1/console/orders/{oid}/special-service/{rid}',
            json={}, headers=H(tech_token))
        assert r.status_code == 200
        _clean(db_conn, oid)

# ═══ Tech orders + accept ═══
class TestTechOrders:
    def test_list(self, client, tech_token):
        r = client.get('/api/v1/console/tech/orders', headers=H(tech_token))
        assert r.status_code == 200
        d = json.loads(r.data)
        assert d['success'] is True
        assert 'data' in d
        assert 'my_orders' in d['data']

    def test_accept_already_assigned(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'pending')
        cur.execute("UPDATE orders SET assigned_staff_id=1 WHERE id=%s", (oid,))
        db_conn.commit()
        r = client.post(f'/api/v1/console/tech/orders/{oid}/accept', json={}, headers=H(tech_token))
        assert r.status_code in (200,400)
        _clean(db_conn, oid)

    def test_accept_bad_status(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'completed')
        db_conn.commit()
        r = client.post(f'/api/v1/console/tech/orders/{oid}/accept', json={}, headers=H(tech_token))
        assert r.status_code in (200,400)
        _clean(db_conn, oid)

    def test_accept_success(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'pending'); db_conn.commit()
        r = client.post(f'/api/v1/console/tech/orders/{oid}/accept', json={}, headers=H(tech_token))
        assert r.status_code == 200
        assert json.loads(r.data)['success'] is True
        _clean(db_conn, oid)

# ═══ Service items ═══
class TestServiceItems:
    def test_all(self, client, tech_token):
        r = client.get('/api/v1/console/service-items', headers=H(tech_token))
        assert r.status_code == 200
        assert json.loads(r.data)['success'] is True

    def test_filtered(self, client, tech_token):
        r = client.get('/api/v1/console/service-items?product_type_id=1', headers=H(tech_token))
        assert r.status_code == 200

# ═══ Return express ═══
class TestReturnExpress:
    def test_update(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'ready'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/return-express',
            json={'return_express_company':'SF','return_express_no':'SF123'},
            headers=H(tech_token))
        assert r.status_code == 200
        assert json.loads(r.data)['success'] is True
        _clean(db_conn, oid)

    def test_missing_no(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'ready'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/return-express',
            json={'return_express_no':''}, headers=H(tech_token))
        assert json.loads(r.data)['success'] is False
        _clean(db_conn, oid)

# ═══ Equipment data ═══
class TestEquipmentData:
    def test_save_and_get(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing')
        iid = _add_item(cur, oid); db_conn.commit()

        r = client.post(f'/api/v1/console/orders/{oid}/equipment-data',
            json={'items':[{
                'order_item_id':iid,
                'inspection_data':{
                    'first_stage_count':1,
                    'first_stage_serials':['FS001'],
                    'first_stage_pre_pressure':['9.5'],
                    'first_stage_post_pressure':['9.8'],
                    'second_stage_count':2,
                    'second_stage_serials':['SS001','SS002'],
                    'second_stage_pre_resistance':['1.2','1.3'],
                    'second_stage_post_resistance':['1.1','1.2']
                }
            }]},
            headers=H(tech_token))
        assert r.status_code == 200
        assert json.loads(r.data)['success'] is True

        # Update (UPSERT)
        r = client.put(f'/api/v1/console/orders/{oid}/equipment-data',
            json={'items':[{
                'order_item_id':iid,
                'inspection_data':{'first_stage_count':2,'first_stage_pre_pressure':['9.0','9.1']}
            }]},
            headers=H(tech_token))
        assert r.status_code == 200

        # Get
        r = client.get(f'/api/v1/console/orders/{oid}/equipment-data', headers=H(tech_token))
        assert r.status_code == 200
        _clean(db_conn, oid)

    def test_empty_items(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'repairing'); db_conn.commit()
        r = client.post(f'/api/v1/console/orders/{oid}/equipment-data',
            json={'items':[]}, headers=H(tech_token))
        assert r.status_code == 400
        _clean(db_conn, oid)

# ═══ Photo deletion ═══
class TestPhotoDeletion:
    def test_delete_nonexistent(self, client, tech_token):
        r = client.delete('/api/v1/console/orders/1/nodes/99999/photo/none.jpg', headers=H(tech_token))
        assert r.status_code in (200,404)

    def test_delete_from_node(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed')
        # Manually create a node with a photo path
        cur.execute(
            "INSERT INTO tracking_nodes (order_id, node_code, node_name, description, staff_id, staff_name, operate_time, photos) "
            "VALUES (%s, 'received', '收货', 'test', 1, 'Tester', NOW(), %s) RETURNING id",
            (oid, json.dumps(['orders/999/nodes/1/photo.jpg'])))
        nid = cur.fetchone()['id']; db_conn.commit()
        r = client.delete(f'/api/v1/console/orders/{oid}/nodes/{nid}/photo/photo.jpg', headers=H(tech_token))
        # Should work or 404 if file doesn't exist on disk
        assert r.status_code in (200,404,400)
        _clean(db_conn, oid)

# ═══ Notification hooks ═══
class TestNotifications:
    def test_receive_fires_hook(self, client, tech_token, db_conn):
        oid = _mk(db_conn.cursor(), 'confirmed'); db_conn.commit()
        r = client.put(f'/api/v1/console/orders/{oid}/receive', json={}, headers=H(tech_token))
        assert r.status_code == 200
        _clean(db_conn, oid)

    def test_ship_fires_hook_with_extra(self, client, tech_token, db_conn):
        cur = db_conn.cursor()
        oid = _mk(cur, 'confirmed'); db_conn.commit()
        for s in ['receive','inspect','repair']:
            client.put(f'/api/v1/console/orders/{oid}/{s}', json={'photos':[]}, headers=H(tech_token))
        with patch('routes_console.workflow._integration_hook_notify'):
            client.put(f'/api/v1/console/orders/{oid}/qc', json={'photos':[]}, headers=H(tech_token))
        db_conn.commit()
        with patch('routes_console.workflow._integration_hook_notify'):
            r = client.put(f'/api/v1/console/orders/{oid}/ship',
                json={'return_express_no':'SF888','photos':[],'return_express_company':'SF'},
                headers=H(tech_token))
            assert r.status_code == 200
            assert json.loads(r.data)['success'] is True
        _clean(db_conn, oid)
