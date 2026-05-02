# -*- coding: utf-8 -*-
"""保养提醒管理测试 — routes_admin/maintenance.py (5 endpoints)"""
import pytest
from datetime import datetime, timedelta


PREFIX = '/api/v1/console/admin'


def _h(token):
    return {'X-Staff-Token': token}


def _make_customer(db_conn, phone='13911111111', name='维护测试客户'):
    cur = db_conn.cursor()
    cur.execute("INSERT INTO customers (phone, name) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING id", (phone, name))
    row = cur.fetchone()
    if row:
        db_conn.commit()
        return row['id']
    cur.execute("SELECT id FROM customers WHERE phone = %s", (phone,))
    cid = cur.fetchone()['id']
    db_conn.commit()
    return cid


def _make_reminder(db_conn, customer_id=None, equipment='测试调节器', status='pending',
                   next_date=None, order_id=None):
    if next_date is None:
        next_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    cur = db_conn.cursor()
    cur.execute('''
        INSERT INTO maintenance_reminders (customer_id, order_id, equipment_summary,
                                          next_service_date, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    ''', (customer_id, order_id, equipment, next_date, status))
    rid = cur.fetchone()['id']
    db_conn.commit()
    return rid


def _cleanup_reminders(db_conn, customer_id=None):
    cur = db_conn.cursor()
    if customer_id:
        cur.execute("DELETE FROM maintenance_reminders WHERE customer_id = %s", (customer_id,))
    else:
        cur.execute("DELETE FROM maintenance_reminders WHERE equipment_summary LIKE '测试%' OR equipment_summary LIKE '新装备%'")
    db_conn.commit()


class TestMaintenanceList:
    def test_list_all(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        rid = _make_reminder(db_conn, customer_id=cid)
        resp = client.get(f'{PREFIX}/maintenance-reminders', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'total' in data
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_list_filter_by_status(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        _make_reminder(db_conn, customer_id=cid, equipment='pending设备', status='pending')
        _make_reminder(db_conn, customer_id=cid, equipment='dismissed设备', status='dismissed')

        resp = client.get(f'{PREFIX}/maintenance-reminders?status=pending', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        for r in data['data']:
            assert r['status'] == 'pending'
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_list_filter_by_customer(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn, name='专属客户')
        _make_reminder(db_conn, customer_id=cid, equipment='专属设备')
        resp = client.get(f'{PREFIX}/maintenance-reminders?customer_id={cid}',
                         headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert any(r['customer_id'] == cid for r in data['data'])
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_list_pagination(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        for i in range(5):
            _make_reminder(db_conn, customer_id=cid, equipment=f'分页设备{i}')

        resp = client.get(f'{PREFIX}/maintenance-reminders?page=1&pageSize=2',
                         headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['data']) <= 2
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_list_no_auth(self, client):
        resp = client.get(f'{PREFIX}/maintenance-reminders')
        assert resp.status_code == 403

    def test_list_non_admin(self, client, tech_token):
        resp = client.get(f'{PREFIX}/maintenance-reminders', headers=_h(tech_token))
        assert resp.status_code == 403


class TestMaintenanceCreate:
    def test_create_valid(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        resp = client.post(f'{PREFIX}/maintenance-reminders',
                          json={'customer_id': cid,
                                'equipment_summary': '新装备调节器',
                                'next_service_date': '2026-08-01'},
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'id' in data
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_create_no_customer(self, client, staff_token):
        resp = client.post(f'{PREFIX}/maintenance-reminders',
                          json={'equipment_summary': '匿名装备',
                                'next_service_date': '2026-08-01'},
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_create_missing_fields(self, client, staff_token):
        resp = client.post(f'{PREFIX}/maintenance-reminders',
                          json={'equipment_summary': ''},
                          headers=_h(staff_token))
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['success'] is False

    def test_create_empty_body(self, client, staff_token):
        resp = client.post(f'{PREFIX}/maintenance-reminders',
                          json={}, headers=_h(staff_token))
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_create_no_auth(self, client):
        resp = client.post(f'{PREFIX}/maintenance-reminders',
                          json={'equipment_summary': 'test'})
        assert resp.status_code == 403


class TestMaintenanceReschedule:
    def test_reschedule_valid(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        rid = _make_reminder(db_conn, customer_id=cid)
        resp = client.put(f'{PREFIX}/maintenance-reminders/{rid}/reschedule',
                         json={'next_service_date': '2026-12-25'},
                         headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_reschedule_missing_date(self, client, staff_token):
        resp = client.put(f'{PREFIX}/maintenance-reminders/99999/reschedule',
                         json={}, headers=_h(staff_token))
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_reschedule_no_auth(self, client):
        resp = client.put(f'{PREFIX}/maintenance-reminders/1/reschedule',
                         json={'next_service_date': '2026-12-25'})
        assert resp.status_code == 403


class TestMaintenanceDismiss:
    def test_dismiss_valid(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        rid = _make_reminder(db_conn, customer_id=cid)
        resp = client.put(f'{PREFIX}/maintenance-reminders/{rid}/dismiss',
                         json={}, headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_dismiss_no_auth(self, client):
        resp = client.put(f'{PREFIX}/maintenance-reminders/1/dismiss', json={})
        assert resp.status_code == 403


class TestMaintenanceStats:
    def test_stats(self, client, staff_token, db_conn):
        cid = _make_customer(db_conn)
        _make_reminder(db_conn, customer_id=cid, status='pending')
        resp = client.get(f'{PREFIX}/maintenance-reminders/stats', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'data' in data
        stats = data['data']
        assert 'total_pending' in stats
        _cleanup_reminders(db_conn, customer_id=cid)

    def test_stats_no_auth(self, client):
        resp = client.get(f'{PREFIX}/maintenance-reminders/stats')
        assert resp.status_code == 403

    def test_stats_non_admin(self, client, tech_token):
        resp = client.get(f'{PREFIX}/maintenance-reminders/stats', headers=_h(tech_token))
        assert resp.status_code == 403
