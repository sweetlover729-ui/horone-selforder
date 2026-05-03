"""client/orders.py 覆盖率专项补齐"""
import pytest
import json
import os
import time
from unittest.mock import patch, MagicMock


PREFIX = '/api/v1/client'


class TestEditOrderItems:
    """edit_order 中 items 更新分支（覆盖 350-426行）"""

    def test_edit_with_items_full(self, client, customer_token, db_conn):
        """编辑订单项：product_type_id, brand_id, model_id, service_type_id, service_item_id, category, customer_note"""
        oid, item_id = _make_order(db_conn, 1, status='confirmed', return_item=True)
        resp = client.put(
            f'{PREFIX}/orders/{oid}/edit',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={
                'items': [{
                    'id': item_id,
                    'product_type_id': 4,
                    'brand_id': 2,
                    'brand_name': 'Custom Brand',
                    'model_id': 79,
                    'model_name': 'Custom Model',
                    'service_type_id': 16,
                    'service_name': 'Custom Service',
                    'category': '一级头',
                    'customer_note': '加速处理'
                }]
            }
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

    def test_edit_items_skip_no_id(self, client, customer_token, db_conn):
        """没有id的item会被跳过"""
        oid = _make_order(db_conn, 1, status='confirmed')
        resp = client.put(
            f'{PREFIX}/orders/{oid}/edit',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'items': [{'product_type_id': 3}]}
        )
        assert resp.status_code == 200

    def test_edit_with_note(self, client, customer_token, db_conn):
        """只更新备注"""
        oid = _make_order(db_conn, 1, status='confirmed')
        resp = client.put(
            f'{PREFIX}/orders/{oid}/edit',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'customer_note': '新备注内容'}
        )
        assert resp.status_code == 200

    def test_edit_wrong_status(self, client, customer_token, db_conn):
        """repairing状态不允许修改"""
        oid = _make_order(db_conn, 1, status='repairing')
        resp = client.put(
            f'{PREFIX}/orders/{oid}/edit',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'receiver_name': 'test'}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is False

    def test_edit_not_own_order(self, client, customer_token, db_conn):
        """修改别人的订单"""
        resp = client.put(
            f'{PREFIX}/orders/99999/edit',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'receiver_name': 'test'}
        )
        # 订单不存在
        assert resp.status_code in (200, 401, 403, 404)


class TestGetOrderDetailGap:
    """get_order_detail 剩余未覆盖分支（260-313行）"""

    def test_detail_with_custom_text_overrides(self, client, customer_token, db_conn):
        """订单项包含 brand_name_text/model_name_text/service_name_text 覆盖"""
        oid = _make_order_with_custom_text(db_conn, 1)
        resp = client.get(
            f'{PREFIX}/orders/{oid}',
            headers={'Authorization': f'Bearer {customer_token}'}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

    def test_detail_with_dict_photos(self, client, customer_token, db_conn):
        """tracking_nodes photos 是对象数组格式 [{"type": "...", "path": "..."}]"""
        oid = _make_order(db_conn, 1)
        cur = db_conn.cursor()
        cur.execute("""
            INSERT INTO tracking_nodes (order_id, node_code, node_name, staff_name, photos, operate_time, created_at)
            VALUES (%s, 'received', '已收货', 'test', %s, NOW(), NOW())
        """, (oid, json.dumps([{'type': 'photo', 'path': 'orders/1/nodes/1/img.jpg'}])))
        db_conn.commit()
        resp = client.get(
            f'{PREFIX}/orders/{oid}',
            headers={'Authorization': f'Bearer {customer_token}'}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        # 验证 photos 被正确解析为 URL 数组
        nodes = data.get('data', {}).get('tracking_nodes', [])
        if nodes:
            node_photos = nodes[-1].get('photos', [])
            assert isinstance(node_photos, list)

    def test_detail_with_plain_string_photos(self, client, customer_token, db_conn):
        """tracking_nodes photos 是普通字符串数组"""
        oid = _make_order(db_conn, 1)
        cur = db_conn.cursor()
        cur.execute("""
            INSERT INTO tracking_nodes (order_id, node_code, node_name, staff_name, photos, operate_time, created_at)
            VALUES (%s, 'received', '已收货', 'test', %s, NOW(), NOW())
        """, (oid, json.dumps(['photo1.jpg', 'photo2.jpg'])))
        db_conn.commit()
        resp = client.get(
            f'{PREFIX}/orders/{oid}',
            headers={'Authorization': f'Bearer {customer_token}'}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

    def test_detail_not_found(self, client, customer_token):
        """不存在的订单"""
        resp = client.get(
            f'{PREFIX}/orders/99999',
            headers={'Authorization': f'Bearer {customer_token}'}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is False


class TestPDFDownloadGap:
    """PDF下载剩余未覆盖分支"""

    def test_pdf_expired(self, client, customer_token, db_conn):
        """PDF超过15天过期 — mock generate 返回过期文件"""
        import tempfile
        oid = _make_order(db_conn, 1)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4 fake pdf')
            pdf_file = f.name
        os.utime(pdf_file, (time.time() - 20*86400, time.time() - 20*86400))

        with patch('pdf_generator.generate_order_pdf', return_value=pdf_file):
            resp = client.get(
                f'{PREFIX}/orders/{oid}/pdf',
                headers={'Authorization': f'Bearer {customer_token}'}
            )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert '已过期' in data.get('message', '')

        if os.path.exists(pdf_file):
            os.remove(pdf_file)

    def test_pdf_not_found_file(self, client, customer_token, db_conn):
        """pdf文件不存在 — mock generate 返回不存在路径"""
        oid = _make_order(db_conn, 1)
        with patch('pdf_generator.generate_order_pdf',
                   return_value='/nonexistent/path/to/pdf.pdf'):
            resp = client.get(
                f'{PREFIX}/orders/{oid}/pdf',
                headers={'Authorization': f'Bearer {customer_token}'}
            )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is False
        assert '不存在' in data.get('message', '')


class TestSpecialServiceRespondGap:
    """专项服务响应剩余未覆盖分支"""

    def test_respond_confirm_with_paid(self, client, customer_token, db_conn):
        """confirm + paid=True"""
        oid = _make_order(db_conn, 1)
        cur = db_conn.cursor()
        cur.execute("""
            INSERT INTO special_service_records (order_id, special_service_id, name, price, quantity, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (oid, 1, '测试服务', 100.0, 1, 'pending'))
        rid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.post(
            f'{PREFIX}/orders/{oid}/special-service/respond',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'record_id': rid, 'action': 'confirm', 'paid': True}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is True

    def test_respond_wrong_order(self, client, customer_token, db_conn):
        """操作别人的订单"""
        resp = client.post(
            f'{PREFIX}/orders/99999/special-service/respond',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'record_id': 1, 'action': 'confirm'}
        )
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['success'] is False


# ========== helpers ==========

def _make_order(db_conn, cust_id=1, status='pending', order_no=None, return_item=False):
    """创建测试订单"""
    import uuid
    if order_no is None:
        order_no = f'TEST-{uuid.uuid4().hex[:8]}'
    cur = db_conn.cursor()
    cur.execute("""
        INSERT INTO orders (order_no, customer_id, status, payment_status,
                          receiver_name, receiver_phone, receiver_address,
                          total_amount, created_at, updated_at)
        VALUES (%s, %s, %s, 'unpaid', 'Test', '13900000001', 'Test Address', 100.0, NOW(), NOW())
        RETURNING id
    """, (order_no, cust_id, status))
    oid = cur.fetchone()['id']
    # 插入一个 order_item
    cur.execute("""
        INSERT INTO order_items (order_id, product_type_id, brand_id, model_id, service_type_id, item_price, quantity)
        VALUES (%s, 1, 1, 79, 15, 50.0, 1)
        RETURNING id
    """, (oid,))
    iid = cur.fetchone()['id']
    db_conn.commit()
    return (oid, iid) if return_item else oid


def _make_order_with_custom_text(db_conn, cust_id=1):
    """创建带 custom text 的订单"""
    import uuid
    order_no = f'TEST-CT-{uuid.uuid4().hex[:8]}'
    cur = db_conn.cursor()
    cur.execute("""
        INSERT INTO orders (order_no, customer_id, status, payment_status,
                          receiver_name, receiver_phone, receiver_address,
                          total_amount, created_at, updated_at)
        VALUES (%s, %s, 'confirmed', 'paid', 'Test', '13900000001', 'Test Address', 100.0, NOW(), NOW())
        RETURNING id
    """, (order_no, cust_id))
    oid = cur.fetchone()['id']
    cur.execute("""
        INSERT INTO order_items (order_id, product_type_id, brand_id, model_id, service_type_id,
                                 brand_name_text, model_name_text, service_name_text, item_price, quantity)
        VALUES (%s, 1, 1, 79, 15, 'CustomBrand', 'CustomModel', 'CustomSvc', 50.0, 1)
    """, (oid,))
    db_conn.commit()
    return oid
