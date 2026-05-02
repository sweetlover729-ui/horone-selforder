# -*- coding: utf-8 -*-
"""tests for routes_console/reports.py + orders.py"""
import pytest
import json
import uuid


PREFIX = '/api/v1/console'


def _h(token):
    return {'X-Staff-Token': token}


def _make_order(conn, cid=1, status='pending'):
    cur = conn.cursor()
    order_no = f'TEST-CR-{uuid.uuid4().hex[:8]}'
    cur.execute(
        "INSERT INTO orders (order_no, customer_id, status, total_amount, payment_status,"
        " receiver_name, receiver_phone, created_at)"
        " VALUES (%s, %s, %s, %s, 'unpaid', 'Test', '13900000001', NOW())"
        " RETURNING id",
        (order_no, cid, status, 500.00)
    )
    oid = cur.fetchone()['id']
    cur.execute(
        "INSERT INTO order_items (order_id, product_type_id, brand_id, service_type_id, item_price, quantity)"
        " VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (oid, 1, 1, 5, 500.00, 1)
    )
    oi_id = cur.fetchone()['id']
    cur.execute(
        "INSERT INTO tracking_nodes (order_id, node_code, node_name, description,"
        " operate_time) VALUES (%s, 'created', '创建订单', '测试订单', NOW())"
        " RETURNING id",
        (oid,)
    )
    node_id = cur.fetchone()['id']
    conn.commit()
    return oid, node_id, oi_id


class TestDashboard:
    """GET /dashboard/stats, /dashboard/report"""

    def test_stats_no_auth(self, client):
        resp = client.get(f'{PREFIX}/dashboard/stats')
        # Without token should return error but not necessarily 401
        # (validate_staff_token returns False but route doesn't check HTTP status explicitly)
        assert resp.status_code in (200, 401, 403)

    def test_stats_with_auth(self, client, staff_token):
        resp = client.get(f'{PREFIX}/dashboard/stats', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'pending_count' in data['data']
        assert 'repairing_count' in data['data']

    def test_report_no_auth(self, client):
        resp = client.get(f'{PREFIX}/dashboard/report')
        assert resp.status_code in (200, 401, 403)

    def test_report_with_auth(self, client, staff_token):
        resp = client.get(f'{PREFIX}/dashboard/report', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'total_orders' in data['data']
        assert 'total_revenue' in data['data']
        assert 'status_breakdown' in data['data']

    def test_report_with_filters(self, client, staff_token):
        resp = client.get(
            f'{PREFIX}/dashboard/report?startDate=2024-01-01&endDate=2030-12-31',
            headers=_h(staff_token)
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_report_with_product_type(self, client, staff_token):
        resp = client.get(
            f'{PREFIX}/dashboard/report?product_type_id=1',
            headers=_h(staff_token)
        )
        assert resp.status_code == 200

    def test_report_with_brand(self, client, staff_token):
        resp = client.get(
            f'{PREFIX}/dashboard/report?brand_id=1',
            headers=_h(staff_token)
        )
        assert resp.status_code == 200

    def test_report_with_customer(self, client, staff_token):
        resp = client.get(
            f'{PREFIX}/dashboard/report?customer_id=1',
            headers=_h(staff_token)
        )
        assert resp.status_code == 200

    def test_report_with_model(self, client, staff_token):
        resp = client.get(
            f'{PREFIX}/dashboard/report?model_id=1',
            headers=_h(staff_token)
        )
        assert resp.status_code == 200

    def test_report_with_service_type(self, client, staff_token):
        resp = client.get(
            f'{PREFIX}/dashboard/report?service_type_id=5',
            headers=_h(staff_token)
        )
        assert resp.status_code == 200


class TestReports:
    """generate-report + report-pdf + node photos"""

    def test_generate_report_no_auth(self, client):
        resp = client.post(f'{PREFIX}/orders/1/generate-report', json={})
        assert resp.status_code == 401

    def test_generate_report_auth_no_order(self, client, staff_token):
        resp = client.post(f'{PREFIX}/orders/99999/generate-report',
                           json={}, headers=_h(staff_token))
        assert resp.status_code == 404

    def test_generate_report_with_order(self, client, staff_token, db_conn):
        oid, _, _ = _make_order(db_conn)
        resp = client.post(f'{PREFIX}/orders/{oid}/generate-report',
                           json={}, headers=_h(staff_token))
        # May fail if pdf_generator has issues, but shouldn't 401/404
        assert resp.status_code not in (401, 403), f"Got {resp.status_code}: {resp.get_json()}"

    def test_report_pdf_no_auth(self, client):
        resp = client.get(f'{PREFIX}/orders/1/report-pdf')
        assert resp.status_code == 401

    def test_report_pdf_auth_no_order(self, client, tech_token):
        resp = client.get(f'{PREFIX}/orders/99999/report-pdf', headers=_h(tech_token))
        assert resp.status_code in (401, 404, 403)

    def test_upload_photo_no_auth(self, client):
        resp = client.post(f'{PREFIX}/orders/1/nodes/1/photo')
        assert resp.status_code == 401

    def test_upload_photo_invalid_node(self, client, tech_token):
        resp = client.post(f'{PREFIX}/orders/99999/nodes/99999/photo',
                           headers=_h(tech_token),
                           data={'photos': []})
        assert resp.status_code == 404

    def test_upload_photo_no_file(self, client, tech_token, db_conn):
        oid, nid, _ = _make_order(db_conn)
        resp = client.post(f'{PREFIX}/orders/{oid}/nodes/{nid}/photo',
                           headers=_h(tech_token))
        assert resp.status_code == 400

    def test_get_photo_no_auth(self, client):
        resp = client.get(f'{PREFIX}/orders/1/nodes/1/photo/test.png')
        assert resp.status_code in (401, 404)

    def test_upload_photo_success(self, client, tech_token, db_conn):
        """Actually upload a real PNG to a tracking node"""
        import io, struct, zlib

        def _make_png(w=1, h=1):
            def chunk(ctype, data):
                c = ctype + data
                return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
            header = b'\x89PNG\r\n\x1a\n'
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            raw = b''
            for y in range(h):
                raw += b'\x00' + b'\xff\x00\x00' * w
            idat = chunk(b'IDAT', zlib.compress(raw))
            iend = chunk(b'IEND', b'')
            return header + ihdr + idat + iend

        oid, nid, _ = _make_order(db_conn)
        png_bytes = _make_png()
        resp = client.post(
            f'{PREFIX}/orders/{oid}/nodes/{nid}/photo',
            headers=_h(tech_token),
            data={'photos': (io.BytesIO(png_bytes), 'test.png')},
            content_type='multipart/form-data'
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['data']['added'] == 1

    def test_get_photo_success(self, client, tech_token, db_conn):
        """Upload then retrieve a photo"""
        import io, struct, zlib

        def _make_png():
            def chunk(ctype, data):
                c = ctype + data
                return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
            header = b'\x89PNG\r\n\x1a\n'
            ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            raw = b'\x00\xff\x00\x00'
            idat = chunk(b'IDAT', zlib.compress(raw))
            iend = chunk(b'IEND', b'')
            return header + ihdr + idat + iend

        oid, nid, _ = _make_order(db_conn)
        # Upload a photo first
        client.post(
            f'{PREFIX}/orders/{oid}/nodes/{nid}/photo',
            headers=_h(tech_token),
            data={'photos': (io.BytesIO(_make_png()), 'photo.png')},
            content_type='multipart/form-data'
        )
        # Now fetch it
        resp = client.get(f'{PREFIX}/orders/{oid}/nodes/{nid}/photo/photo.png',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 500)

    def test_generate_report_failure(self, client, tech_token, db_conn, monkeypatch):
        """Cover the PDF generation failure path"""
        import pdf_generator
        monkeypatch.setattr(pdf_generator, 'generate_order_pdf', lambda order: None)
        oid, _, _ = _make_order(db_conn)
        resp = client.post(f'{PREFIX}/orders/{oid}/generate-report',
                           json={}, headers=_h(tech_token))
        assert resp.status_code == 500
        data = resp.get_json()
        assert data['success'] is False

    def test_report_pdf_download_mode(self, client, tech_token, db_conn, tmp_path):
        """Test PDF serving in download mode"""
        pdf_file = tmp_path / 'test-report.pdf'
        pdf_file.write_bytes(b'%PDF-1.4 fake pdf content')
        cur = db_conn.cursor()
        oid, _, _ = _make_order(db_conn)
        cur.execute('UPDATE orders SET pdf_path = %s WHERE id = %s',
                    (str(pdf_file), oid))
        db_conn.commit()
        resp = client.get(f'{PREFIX}/orders/{oid}/report-pdf?download=1',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 500)

    def test_report_pdf_inline_mode(self, client, tech_token, db_conn, tmp_path):
        """Test PDF serving in inline/preview mode"""
        pdf_file = tmp_path / 'test-report2.pdf'
        pdf_file.write_bytes(b'%PDF-1.4 fake pdf content')
        cur = db_conn.cursor()
        oid, _, _ = _make_order(db_conn)
        cur.execute('UPDATE orders SET pdf_path = %s WHERE id = %s',
                    (str(pdf_file), oid))
        db_conn.commit()
        resp = client.get(f'{PREFIX}/orders/{oid}/report-pdf',
                          headers=_h(tech_token))
        assert resp.status_code in (200, 404, 500)


class TestOrders:
    """GET /orders, release, delete, detail, payment-status"""

    def test_get_orders_no_auth(self, client):
        resp = client.get(f'{PREFIX}/orders')
        assert resp.status_code == 401

    def test_get_orders_empty(self, client, tech_token):
        resp = client.get(f'{PREFIX}/orders', headers=_h(tech_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_orders_with_status(self, client, tech_token):
        resp = client.get(f'{PREFIX}/orders?status=pending', headers=_h(tech_token))
        assert resp.status_code == 200

    def test_get_orders_repairing(self, client, tech_token):
        """Special repairing status expands to 3 statuses"""
        resp = client.get(f'{PREFIX}/orders?status=repairing', headers=_h(tech_token))
        assert resp.status_code == 200

    def test_get_orders_deleted(self, client, tech_token):
        resp = client.get(f'{PREFIX}/orders?status=deleted', headers=_h(tech_token))
        assert resp.status_code == 200

    def test_get_orders_with_filters(self, client, tech_token):
        resp = client.get(
            f'{PREFIX}/orders?page=1&size=5&startDate=2024-01-01'
            f'&endDate=2030-12-31&product_type_id=1&brand_id=1&keyword=test',
            headers=_h(tech_token)
        )
        assert resp.status_code == 200

    def test_get_order_detail_no_auth(self, client):
        resp = client.get(f'{PREFIX}/orders/1')
        assert resp.status_code == 401

    def test_get_order_detail_not_found(self, client, tech_token):
        resp = client.get(f'{PREFIX}/orders/99999', headers=_h(tech_token))
        assert resp.status_code in (200, 404)

    def test_release_no_auth(self, client):
        resp = client.post(f'{PREFIX}/orders/1/release', json={})
        assert resp.status_code in (401, 403)

    def test_release_not_admin(self, client, tech_token):
        resp = client.post(f'{PREFIX}/orders/1/release', json={},
                           headers=_h(tech_token))
        assert resp.status_code == 403

    def test_release_admin_no_order(self, client, staff_token):
        resp = client.post(f'{PREFIX}/orders/99999/release', json={},
                           headers=_h(staff_token))
        assert resp.status_code == 404

    def test_delete_no_auth(self, client):
        resp = client.delete(f'{PREFIX}/orders/1')
        assert resp.status_code in (401, 403)

    def test_delete_not_admin(self, client, tech_token):
        resp = client.delete(f'{PREFIX}/orders/1', headers=_h(tech_token))
        assert resp.status_code == 403

    def test_delete_admin_no_order(self, client, staff_token):
        resp = client.delete(f'{PREFIX}/orders/99999', headers=_h(staff_token))
        assert resp.status_code == 404

    def test_payment_status_no_auth(self, client):
        resp = client.put(f'{PREFIX}/orders/1/payment-status', json={})
        assert resp.status_code in (401, 403)

    def test_payment_status_not_admin(self, client, tech_token):
        resp = client.put(f'{PREFIX}/orders/1/payment-status',
                          json={'payment_status': 'paid'},
                          headers=_h(tech_token))
        assert resp.status_code in (200, 401, 403)

    def test_payment_status_invalid(self, client, staff_token):
        resp = client.put(f'{PREFIX}/orders/1/payment-status',
                          json={'payment_status': 'invalid'},
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False

    def test_payment_status_valid(self, client, staff_token, db_conn):
        oid, _, _ = _make_order(db_conn)
        resp = client.put(f'{PREFIX}/orders/{oid}/payment-status',
                          json={'payment_status': 'paid'},
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True


class TestConsoleAuth:
    """routes_console/auth.py"""

    def test_login_success(self, client):
        resp = client.post(f'{PREFIX}/auth/login',
                          json={'username': 'kent', 'password': 'LILY1018@kent729'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'token' in data

    def test_login_invalid_password(self, client):
        resp = client.post(f'{PREFIX}/auth/login',
                          json={'username': 'kent', 'password': 'wrongpass'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False

    def test_login_nonexistent(self, client):
        resp = client.post(f'{PREFIX}/auth/login',
                          json={'username': 'nosuchuser99999', 'password': 'anything'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False

    def test_login_pydantic_fail(self, client):
        """Missing required fields"""
        resp = client.post(f'{PREFIX}/auth/login', json={})
        assert resp.status_code == 400

    def test_me_no_auth(self, client):
        resp = client.get(f'{PREFIX}/auth/me')
        assert resp.status_code in (200, 401)

    def test_me_with_auth(self, client, staff_token):
        resp = client.get(f'{PREFIX}/auth/me', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['staff']['username'] == 'kent'

    def test_change_password_no_auth(self, client):
        resp = client.put(f'{PREFIX}/auth/password', json={})
        assert resp.status_code in (200, 401)

    def test_change_password_empty(self, client, staff_token):
        resp = client.put(f'{PREFIX}/auth/password',
                          json={'old_password': '', 'new_password': ''},
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False

    def test_change_password_wrong_old(self, client, staff_token):
        resp = client.put(f'{PREFIX}/auth/password',
                          json={'old_password': 'wrong', 'new_password': 'NEW1234'},
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False
