# -*- coding: utf-8 -*-
"""backup_restore.py 专项测试 — 覆盖剩余的 44 行（67%→目标95%+）"""
import pytest
import json as _json
from datetime import datetime, timedelta

API = '/api/v1/console/admin'

def _h(token):
    return {'X-Staff-Token': token}


class TestBackupExport:
    """GET /backup — 导出全库"""

    def test_export_no_token(self, client):
        resp = client.get(f'{API}/backup')
        assert resp.status_code == 403

    def test_export_success(self, client, staff_token):
        resp = client.get(f'{API}/backup', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'tables' in data
        assert 'exported_at' in data
        for t in ['product_types', 'brands', 'staff', 'orders']:
            assert t in data['tables']


class TestBackupRestore:
    """POST /backup/restore — 从JSON恢复"""

    def test_restore_no_token(self, client):
        resp = client.post(f'{API}/backup/restore',
                           json={'confirm': True, 'tables': {}})
        assert resp.status_code == 403

    def test_restore_no_confirm(self, client, staff_token):
        resp = client.post(f'{API}/backup/restore',
                           json={'confirm': False, 'tables': {}},
                           headers=_h(staff_token))
        assert resp.status_code == 400
        assert 'confirm' in resp.get_json().get('message', '').lower()

    def test_restore_empty_tables(self, client, staff_token):
        resp = client.post(f'{API}/backup/restore',
                           json={'confirm': True, 'tables': {}},
                           headers=_h(staff_token))
        assert resp.status_code == 400

    def test_restore_full_roundtrip(self, client, staff_token):
        """Export全部数据 → Restore同样数据（no-op回环），覆盖TRUNCATE/INSERT/SETVAL"""
        # 1. 导出
        export_resp = client.get(f'{API}/backup', headers=_h(staff_token))
        assert export_resp.status_code == 200
        backup_data = export_resp.get_json()

        # 2. 恢复
        restore_resp = client.post(f'{API}/backup/restore',
                                   json={'confirm': True, 'tables': backup_data['tables']},
                                   headers=_h(staff_token))
        assert restore_resp.status_code == 200
        result = restore_resp.get_json()
        assert result['success'] is True
        assert 'results' in result

        # 验证各表已恢复
        for table, info in result['results'].items():
            assert 'imported' in info, f'{table} 缺少 imported 字段'


class TestArchiveCleanup:
    """POST /archive-cleanup — 15天后归档"""

    def test_archive_no_token(self, client):
        resp = client.post(f'{API}/archive-cleanup', json={})
        assert resp.status_code == 403

    def test_archive_non_admin(self, client, tech_token):
        resp = client.post(f'{API}/archive-cleanup', json={},
                           headers=_h(tech_token))
        assert resp.status_code == 403

    def test_archive_no_matching_orders(self, client, staff_token):
        """没有订单匹配15天条件"""
        resp = client.post(f'{API}/archive-cleanup', json={},
                           headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert '0' in data['message']  # "处理 0 个订单"

    def test_archive_with_matching_orders(self, client, staff_token, db_conn):
        """有订单匹配15天条件 → 覆盖 UPDATE + 文件清理"""
        # 在seed数据基础上插入已完成16天的订单
        cursor = db_conn.cursor()

        # 找现有 customer
        cursor.execute("SELECT id FROM customers LIMIT 1")
        cust = cursor.fetchone()
        if not cust:
            cursor.execute("INSERT INTO customers (phone, name) VALUES ('13900000000', 'test') RETURNING id")
            cust = cursor.fetchone()
        customer_id = cust['id']

        # 插入已完成 16 天的订单
        sixteen_days_ago = (datetime.now() - timedelta(days=16)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO orders (order_no, customer_id, status, payment_status,
                               completed_at, archived, total_amount, receiver_name, receiver_phone)
            VALUES (%s, %s, 'completed', 'paid', %s, 0, 0, 'test', '13900000000')
            RETURNING id
        """, (f'ARC-TEST-{datetime.now().strftime("%H%M%S")}', customer_id, sixteen_days_ago))
        order_id = cursor.fetchone()['id']

        # 插入 tracking_nodes
        cursor.execute("""
            INSERT INTO tracking_nodes (order_id, node_code, node_name, photos, description, operate_note, staff_name, operate_time)
            VALUES (%s, 'completed', '完成', %s, 'test desc', 'test note', 'kent', NOW())
        """, (order_id, '["test.jpg"]'))

        # 插入 special_service_records
        cursor.execute("""
            INSERT INTO special_service_records (order_id, name, price, staff_photos, description, staff_note, created_at)
            VALUES (%s, 'test service', 100, '["sp.jpg"]', 'sp desc', 'sp note', NOW())
        """, (order_id,))

        db_conn.commit()

        # 3. 执行归档
        resp = client.post(f'{API}/archive-cleanup', json={},
                           headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

        # 4. 验证订单已归档
        cursor2 = db_conn.cursor()
        cursor2.execute("SELECT archived FROM orders WHERE id = %s", (order_id,))
        row = cursor2.fetchone()
        assert row['archived'] == 1

        # 5. 验证 tracking_nodes 照片/描述已清空（photos 是 text 列，存字符串）
        cursor2.execute("SELECT photos, description, operate_note FROM tracking_nodes WHERE order_id = %s", (order_id,))
        tn = cursor2.fetchone()
        assert tn['photos'] == '[]'
        assert tn['description'] == ''
        assert tn['operate_note'] == ''

        # 6. 验证 special_service_records 已清理
        cursor2.execute("SELECT staff_photos, description, staff_note FROM special_service_records WHERE order_id = %s", (order_id,))
        sr = cursor2.fetchone()
        assert sr['staff_photos'] == '[]'
        assert sr['description'] == ''
        assert sr['staff_note'] == ''

        # 清理
        cursor.execute("DELETE FROM special_service_records WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM tracking_nodes WHERE order_id = %s", (order_id,))
        cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        db_conn.commit()
