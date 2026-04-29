# -*- coding: utf-8 -*-
"""State machine transition tests — the most critical business logic.

Covers workflow step transitions, UPSERT guard logic, status change
logging, and idempotent re-submission (the bugs found in the audit).
"""
import pytest
import json
import database


def _cleanup_order(conn, order_id):
    """Delete test order and its tracking nodes (best-effort)."""
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_order(client, customer_token):
    """Create a minimal order via the client API, returns order_id."""
    resp = client.post('/api/v1/client/orders',
                       json={
                           'items': [{
                               'product_type_id': 1,
                               'brand_id': 1,
                               'model_id': 79,
                               'service_type_id': 15,
                               'quantity': 1,
                           }],
                           'delivery_type': 'store',
                           'receiver_name': '测试',
                           'receiver_phone': '13900000001',
                       },
                       headers={'Authorization': customer_token})
    data = resp.get_json()
    assert data['success'], f'create order failed: {data}'
    order_id = data.get('order_id') or data.get('data', {}).get('id')
    assert order_id, f'no order_id in response: {data}'
    return order_id


def _accept_order(client, tech_token, order_id):
    """Tech accepts the order."""
    resp = client.post(f'/api/v1/console/tech/orders/{order_id}/accept',
                       headers={'X-Staff-Token': tech_token})
    data = resp.get_json()
    assert data['success'], f'accept order failed: {data}'


def _submit_step(client, staff_token, url_suffix, payload=None):
    """Submit a workflow step and return JSON response."""
    resp = client.put(f'/api/v1/console/orders{url_suffix}',
                       json=payload or {},
                       headers={'X-Staff-Token': staff_token})
    return resp, resp.get_json()

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWorkflowStateMachine:

    def test_full_workflow_transitions(self, client, customer_token, tech_token):
        """End-to-end: all 6 steps complete without errors."""
        order_id = _create_order(client, customer_token)
        try:
            # Step 0: accept
            _accept_order(client, tech_token, order_id)

            # Step 1: receive → received
            resp, data = _submit_step(client, tech_token, f'/{order_id}/receive')
            assert resp.status_code == 200
            assert data['success']

            # Step 2: inspect → inspecting
            resp, data = _submit_step(client, tech_token, f'/{order_id}/inspect',
                                      {'note': '拆件检验完成', 'photos': []})
            assert resp.status_code == 200
            assert data['success']

            # Step 3: repair → repairing → ready
            resp, data = _submit_step(client, tech_token, f'/{order_id}/repair',
                                      {'note': '维修完成', 'selected_items': [],
                                       'photos': [], 'complete': True})
            assert resp.status_code == 200
            assert data['success']

            # Step 4: QC → ready (re-submit with complete → ready)
            resp, data = _submit_step(client, tech_token, f'/{order_id}/qc',
                                      {'note': '质检合格', 'photos': []})
            assert resp.status_code == 200
            assert data['success'] or 'already_done' in data

            # Step 5: ship → shipped
            resp, data = _submit_step(client, tech_token, f'/{order_id}/ship',
                                      {'express_company': '顺丰', 'express_no': 'SF12345678'})
            assert resp.status_code == 200
            assert data['success']

            # Step 6: complete → completed
            resp, data = _submit_step(client, tech_token, f'/{order_id}/complete')
            assert resp.status_code == 200
            assert data['success']

        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # UPSERT idempotency tests (the bug fixed on 04-26)
    # ══════════════════════════════════════════════════════════════════════

    def test_inspect_upert_allows_resubmit(self, client, customer_token, tech_token):
        """Submitting inspect twice with same status should NOT return
        already_done — it should update the note and photos."""
        order_id = _create_order(client, customer_token)
        try:
            _accept_order(client, tech_token, order_id)
            _submit_step(client, tech_token, f'/{order_id}/receive')

            # First inspect
            resp, d1 = _submit_step(client, tech_token, f'/{order_id}/inspect',
                                    {'note': '第一版检验', 'photos': []})
            assert d1['success'], f'inspect 1 failed: {d1}'

            # Second inspect — same status, should NOT get already_done
            resp, d2 = _submit_step(client, tech_token, f'/{order_id}/inspect',
                                    {'note': '第二版检验（修改）', 'photos': []})
            assert d2['success'], f'inspect 2 failed: {d2}'
            assert not d2.get('already_done'), \
                f'UPSERT should NOT return already_done for same-status resubmit: {d2}'

        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()

    def test_receive_upert_allows_resubmit(self, client, customer_token, tech_token):
        """Submitting receive twice with same status should work."""
        order_id = _create_order(client, customer_token)
        try:
            _accept_order(client, tech_token, order_id)

            resp, d1 = _submit_step(client, tech_token, f'/{order_id}/receive')
            assert d1['success']

            resp, d2 = _submit_step(client, tech_token, f'/{order_id}/receive',
                                    {'photos': []})
            assert d2['success']
            assert not d2.get('already_done'), \
                f'UPSERT should NOT return already_done for same-status resubmit: {d2}'

        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # Status change logging
    # ══════════════════════════════════════════════════════════════════════

    def test_status_change_logged_on_transitions(self, client, customer_token, tech_token):
        """Every status transition creates a status_change_log row."""
        order_id = _create_order(client, customer_token)
        try:
            _accept_order(client, tech_token, order_id)
            _submit_step(client, tech_token, f'/{order_id}/receive')
            _submit_step(client, tech_token, f'/{order_id}/inspect',
                         {'note': 'ok', 'photos': []})

            conn = database.get_connection()
            cur = conn.cursor()
            cur.execute(
                'SELECT field, old_value, new_value FROM status_change_log '
                'WHERE order_id = %s ORDER BY id',
                (order_id,))
            rows = cur.fetchall()
            conn.close()

            fields = [(r['field'], r['old_value'], r['new_value']) for r in rows]
            # Must contain at least: received, inspecting
            status_changes = [r for r in fields if r[0] == 'status']
            assert len(status_changes) >= 2, \
                f'Expected >=2 status log entries, got {len(status_changes)}: {fields}'

        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()

    # ══════════════════════════════════════════════════════════════════════
    # Constraint / guard tests
    # ══════════════════════════════════════════════════════════════════════

    def test_cannot_ship_before_ready(self, client, customer_token, tech_token):
        """Shipping an order that hasn't reached 'ready' should fail."""
        order_id = _create_order(client, customer_token)
        try:
            _accept_order(client, tech_token, order_id)
            _submit_step(client, tech_token, f'/{order_id}/receive')

            resp, data = _submit_step(client, tech_token, f'/{order_id}/ship',
                                      {'express_company': '顺丰', 'express_no': 'SF123'})
            # Should fail: status is 'received', not 'ready'
            assert resp.status_code == 400 or not data.get('success'), \
                f'Shipping before ready should fail: {data}'

        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()


class TestAuthEndpoints:

    def test_staff_login_success(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'kent', 'password': 'LILY1018@kent729'})
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success']
        assert 'token' in data

    def test_staff_login_bad_password(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'kent', 'password': 'wrong'})
        data = resp.get_json()
        assert resp.status_code == 401 or not data.get('success')

    def test_unauthenticated_access_rejected(self, client):
        resp = client.get('/api/v1/console/orders')
        assert resp.status_code in (401, 403)


class TestHealthCheck:

    def test_health_returns_ok(self, client):
        resp = client.get('/health')
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['success']
        assert data['database'] == 'ok'


class TestAdminSecurity:
    """Verify admin routes are properly authenticated."""

    def _login(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'kent', 'password': 'LILY1018@kent729'})
        return resp.get_json()['token']

    # ── Maintenance endpoints (fixed 04-29) ──

    def test_maintenance_list_rejected_without_auth(self, client):
        resp = client.get('/api/v1/console/admin/maintenance-reminders')
        assert resp.status_code in (401, 403), f'Expected 401/403, got {resp.status_code}'

    def test_maintenance_list_ok_with_auth(self, client):
        token = self._login(client)
        resp = client.get('/api/v1/console/admin/maintenance-reminders',
                          headers={'X-Staff-Token': token})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success']

    def test_maintenance_stats_rejected_without_auth(self, client):
        resp = client.get('/api/v1/console/admin/maintenance-reminders/stats')
        assert resp.status_code in (401, 403), f'Expected 401/403, got {resp.status_code}'

    def test_maintenance_create_rejected_without_auth(self, client):
        resp = client.post('/api/v1/console/admin/maintenance-reminders',
                           json={'equipment_summary': 'test', 'next_service_date': '2026-05-01'})
        assert resp.status_code in (401, 403), f'Expected 401/403, got {resp.status_code}'

    # ── Catalog endpoints ──

    def test_catalog_list_rejected_without_auth(self, client):
        resp = client.get('/api/v1/console/admin/product-types')
        assert resp.status_code in (401, 403), f'Expected 401/403, got {resp.status_code}'

    # ── Staff endpoints ──

    def test_staff_list_rejected_without_auth(self, client):
        resp = client.get('/api/v1/console/admin/staff')
        assert resp.status_code in (401, 403), f'Expected 401/403, got {resp.status_code}'


class TestClientPublicRoutes:
    """Verify client public browsing works without auth."""

    def test_product_types_public(self, client):
        resp = client.get('/api/v1/client/product-types')
        data = resp.get_json()
        # May return success or not depending on DB state, but shouldn't be auth error
        assert resp.status_code not in (401, 403), \
            f'Product types should be public, got {resp.status_code}: {data}'

    def test_brands_public(self, client):
        resp = client.get('/api/v1/client/brands')
        assert resp.status_code not in (401, 403), \
            f'Brands should be public, got {resp.status_code}'

    def test_services_public(self, client):
        resp = client.get('/api/v1/client/services')
        assert resp.status_code not in (401, 403), \
            f'Services should be public, got {resp.status_code}'

    def test_client_orders_rejected_without_auth(self, client):
        """Client orders endpoint should require customer auth."""
        resp = client.post('/api/v1/client/orders', json={})
        # Client endpoints return 200 with success=False for auth failures
        # (inconsistent with console endpoints which return 401)
        if resp.status_code == 200:
            data = resp.get_json()
            assert not data.get('success'), \
                f'Client orders should reject without auth: {data}'
        else:
            assert resp.status_code in (401, 403), \
                f'Client orders require auth, got {resp.status_code}'


class TestWorkflowEdgeCases:
    """Edge cases for the workflow state machine."""

    def _login(self, client):
        resp = client.post('/api/v1/console/auth/login',
                           json={'username': 'kent', 'password': 'LILY1018@kent729'})
        return resp.get_json()['token']

    def test_complete_before_ship_fails(self, client, customer_token, tech_token):
        """Cannot complete an order that hasn't been shipped."""
        order_id = _create_order(client, customer_token)
        try:
            _accept_order(client, tech_token, order_id)
            _submit_step(client, tech_token, f'/{order_id}/receive')

            # Try to complete before ship
            resp, data = _submit_step(client, tech_token, f'/{order_id}/complete')
            assert resp.status_code == 400 or not data.get('success'), \
                f'Complete before ship should fail: {data}'
        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()

    def test_order_not_found_returns_404(self, client):
        token = self._login(client)
        resp = client.get('/api/v1/console/orders/99999',
                          headers={'X-Staff-Token': token})
        # Accept either 404 or 200 with success=False (API returns business error)
        if resp.status_code == 200:
            data = resp.get_json()
            assert not data.get('success'), \
                f'Order 99999 should not exist: {data}'
        else:
            assert resp.status_code == 404

    def test_double_accept_is_idempotent(self, client, customer_token, tech_token):
        """Accepting an order twice should succeed (idempotent)."""
        order_id = _create_order(client, customer_token)
        try:
            resp1 = client.post(f'/api/v1/console/tech/orders/{order_id}/accept',
                                headers={'X-Staff-Token': tech_token})
            assert resp1.status_code == 200

            resp2 = client.post(f'/api/v1/console/tech/orders/{order_id}/accept',
                                headers={'X-Staff-Token': tech_token})
            data2 = resp2.get_json()
            # Should succeed (idempotent), potentially with already_assigned or accepted
            assert data2.get('success') or resp2.status_code == 200, \
                f'Double accept should be idempotent: {data2}'
        finally:
            conn = database.get_connection()
            _cleanup_order(conn, order_id)
            conn.close()
# ============================================================
# TestClientAuth — 客户端认证测试
# ============================================================
class TestClientAuth:
    """客户端认证：手机号登录（含新用户自动注册）"""

    def test_phone_login_new_user(self, client):
        """新手机号登录 → 自动注册并返回 token"""
        import time
        phone = f'139{int(time.time()) % 100000000:08d}'
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': phone, 'name': '自动注册用户'})
        data = resp.get_json()
        assert data['success'], f'phone-login failed: {data}'
        info = data['data']
        assert info['phone'] == phone
        assert info['name'] == '自动注册用户'
        assert len(info['token']) > 10, 'token too short'

    def test_phone_login_existing_user(self, client):
        """已注册用户再次登录 → 同 customer_id + 新 token"""
        resp1 = client.post('/api/v1/client/auth/phone-login',
                            json={'phone': '13900000001', 'name': '测试客户'})
        data1 = resp1.get_json()
        assert data1['success'], f'first login failed: {data1}'
        cust_id = data1['data']['id']
        token1 = data1['data']['token']

        resp2 = client.post('/api/v1/client/auth/phone-login',
                            json={'phone': '13900000001', 'name': '测试客户'})
        data2 = resp2.get_json()
        assert data2['success'], f'second login failed: {data2}'
        assert data2['data']['id'] == cust_id, 'customer id should match'
        assert data2['data']['token'] != token1, 'token should be regenerated'

    def test_phone_login_missing_params(self, client):
        """缺少参数 → 返回错误"""
        resp = client.post('/api/v1/client/auth/phone-login', json={})
        data = resp.get_json()
        assert not data['success']
        assert '手机号' in data.get('message', '') or 'characters' in data.get('message', '').lower()

        resp2 = client.post('/api/v1/client/auth/phone-login',
                            json={'phone': '13900000002'})
        data2 = resp2.get_json()
        assert resp2.status_code in (200, 400), f'unexpected status: {resp2.status_code}'

    def test_phone_login_token_is_usable(self, client):
        """登录后 token 可用于后续 API 请求"""
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': '13900000001', 'name': '测试客户'})
        data = resp.get_json()
        assert data['success']
        token = data['data']['token']

        # Use token to list own orders
        resp2 = client.get('/api/v1/client/orders/my',
                           headers={'Authorization': f'Bearer {token}'})
        data2 = resp2.get_json()
        assert data2['success'], f'order list with token failed: {data2}'


# ============================================================
# TestClientOrderFlow — 客户端订单全流程
# ============================================================
class TestClientOrderFlow:
    """客户端：创建订单 → 列表 → 详情 → 取消"""

    @staticmethod
    def _login(client):
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': '13900000001', 'name': '测试客户'})
        data = resp.get_json()
        assert data['success'], f'login failed: {data}'
        return data['data']['token'], data['data']['id']

    @staticmethod
    def _auth(token):
        return {'Authorization': f'Bearer {token}'}

    def _create_and_cancel(self, client, token, **overrides):
        """Helper: create order, return data; caller must cancel"""
        h = self._auth(token)
        payload = {
            'items': [{
                'product_type_id': 1,
                'service_type_id': 15,
                'brand_id': 1,
                'model_name': 'TestModel',
            }],
            'delivery_type': 'store',
            'receiver_name': '测试收件人',
            'receiver_phone': '13900000001',
            'customer_note': '测试备注',
        }
        payload.update(overrides)
        resp = client.post('/api/v1/client/orders', json=payload, headers=h)
        return resp.get_json()

    def test_create_order_minimal(self, client):
        """最小参数创建订单"""
        token, _ = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'items': [{
                'product_type_id': 1,
                'service_type_id': 15,
            }],
            'delivery_type': 'store',
        }, headers=h)

        data = resp.get_json()
        assert data['success'], f'create order failed: {data}'
        order = data['data']
        assert order['id'] is not None
        assert order['order_no']
        assert order['status'] in ('confirmed', 'created')
        assert 'SIM' in order['order_no'] or 'RMD' in order['order_no']

        client.put(f"/api/v1/client/orders/{order['id']}/cancel", headers=h)

    def test_create_order_full_fields(self, client):
        """完整字段创建订单"""
        token, _ = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'items': [{
                'product_type_id': 1,
                'service_type_id': 15,
                'brand_id': 1,

                'model_name': 'FullTestModel',
                'brand_name': 'Scubapro',
                'quantity': 2,
            }],
            'delivery_type': 'express',
            'receiver_name': '张测试',
            'receiver_phone': '13800001111',
            'receiver_address': '广东省深圳市南山区科技园',

            'customer_note': '请使用原厂配件',
        }, headers=h)

        data = resp.get_json()
        assert data['success'], f'create full order failed: {data}'
        order = data['data']
        assert order['total_amount'] is not None
        assert float(order['total_amount']) >= 0

        client.put(f"/api/v1/client/orders/{order['id']}/cancel", headers=h)

    def test_create_order_missing_items(self, client):
        """缺少 items 字段 → 返回错误"""
        token, _ = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'delivery_type': 'store',
        }, headers=h)

        data = resp.get_json()
        assert not data['success'], f'should reject order without items: {data}'

    def test_list_orders(self, client):
        """客户端订单列表"""
        token, _ = self._login(client)
        h = self._auth(token)

        data_c = self._create_and_cancel(client, token)
        if not data_c['success']:
            pytest.skip(f'Cannot create test order: {data_c}')
        oid = data_c['data']['id']

        try:
            resp = client.get('/api/v1/client/orders/my', headers=h)
            data = resp.get_json()
            assert data['success'], f'list orders failed: {data}'
            orders = data.get('data', data.get('orders', []))
            assert len(orders) > 0, 'order list should not be empty'
            found = any(o['id'] == oid for o in orders)
            assert found, f'created order {oid} not found in list'
        finally:
            client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h)

    def test_order_detail(self, client):
        """客户端订单详情"""
        token, _ = self._login(client)
        h = self._auth(token)

        data_c = self._create_and_cancel(client, token)
        if not data_c['success']:
            pytest.skip(f'Cannot create test order: {data_c}')
        oid = data_c['data']['id']

        try:
            resp = client.get(f'/api/v1/client/orders/{oid}', headers=h)
            data = resp.get_json()
            assert data['success'], f'get order detail failed: {data}'
            order = data['data']
            assert order['id'] == oid
        finally:
            client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h)

    def test_cancel_order(self, client):
        """取消订单 → 状态变为 cancelled"""
        token, _ = self._login(client)
        h = self._auth(token)

        data_c = self._create_and_cancel(client, token)
        if not data_c['success']:
            pytest.skip(f'Cannot create test order: {data_c}')
        oid = data_c['data']['id']

        resp = client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h)
        data = resp.get_json()
        assert data['success'], f'cancel failed: {data}'

        resp2 = client.get(f'/api/v1/client/orders/{oid}', headers=h)
        data2 = resp2.get_json()
        assert data2['success']
        assert data2['data']['status'] in ('cancelled', 'canceled'), \
            f"status should be cancelled, got: {data2['data']['status']}"

    def test_cancel_already_cancelled(self, client):
        """重复取消 → 返回错误"""
        token, _ = self._login(client)
        h = self._auth(token)

        data_c = self._create_and_cancel(client, token)
        if not data_c['success']:
            pytest.skip(f'Cannot create test order: {data_c}')
        oid = data_c['data']['id']

        client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h)

        resp2 = client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h)
        data2 = resp2.get_json()
        assert not data2['success'] or '已取消' in str(data2), \
            f'double cancel should be rejected: {data2}'

    def test_unauthorized_access(self, client):
        """无 token 访问客户端接口 → 返回失败"""
        resp = client.get('/api/v1/client/orders/my')
        data = resp.get_json()
        assert not data['success'], f'should reject unauthenticated: {data}'
        assert 'token' in data.get('message', '').lower() or '登录' in data.get('message', '')

    def test_invalid_token_access(self, client):
        """无效 token 访问客户端接口 → 返回失败"""
        resp = client.get('/api/v1/client/orders/my',
                          headers={'Authorization': 'Bearer invalid-token-12345'})
        data = resp.get_json()
        assert not data['success'], f'should reject invalid token: {data}'

    def test_other_customer_cannot_access(self, client):
        """客户 A 不能访问客户 B 的订单"""
        resp_a = client.post('/api/v1/client/auth/phone-login',
                             json={'phone': '13900000001', 'name': '测试客户'})
        token_a = resp_a.get_json()['data']['token']

        resp_b = client.post('/api/v1/client/auth/phone-login',
                             json={'phone': '13900000002', 'name': '其他客户'})
        token_b = resp_b.get_json()['data']['token']

        # User B creates order
        h_b = {'Authorization': f'Bearer {token_b}'}
        resp_create = client.post('/api/v1/client/orders', json={
            'items': [{'product_type_id': 1, 'service_type_id': 15}],
            'delivery_type': 'store',
        }, headers=h_b)
        assert resp_create.get_json()['success']
        oid = resp_create.get_json()['data']['id']

        try:
            # User A tries to access user B's order
            h_a = {'Authorization': f'Bearer {token_a}'}
            resp = client.get(f'/api/v1/client/orders/{oid}', headers=h_a)
            data = resp.get_json()
            assert not data['success'], \
                f'customer A should not access customer B order: {data}'
        finally:
            client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h_b)


# ============================================================
# TestEdgeCases — 边界条件与安全
# ============================================================
class TestEdgeCases:
    """边界条件：特殊字符、超长输入、SQL 注入防护"""

    @staticmethod
    def _login(client):
        resp = client.post('/api/v1/client/auth/phone-login',
                           json={'phone': '13900000001', 'name': '测试客户'})
        data = resp.get_json()
        assert data['success']
        return data['data']['token']

    @staticmethod
    def _auth(token):
        return {'Authorization': f'Bearer {token}'}

    def test_special_characters_in_note(self, client):
        """customer_note 含 emoji / HTML / 引号"""
        token = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'items': [{'product_type_id': 1, 'service_type_id': 15}],
            'delivery_type': 'store',
            'customer_note': '\u26a0 注意 <script>alert(1)</script> "引号" \'单引号\'',
        }, headers=h)
        assert resp.status_code < 500, 'Server should not 500 on special chars'
        data = resp.get_json()
        if data.get('success'):
            client.put(f"/api/v1/client/orders/{data['data']['id']}/cancel", headers=h)

    def test_very_long_note(self, client):
        """超长备注 (~30KB)"""
        token = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'items': [{'product_type_id': 1, 'service_type_id': 15}],
            'delivery_type': 'store',
            'customer_note': '测试内容' * 5000,
        }, headers=h)
        assert resp.status_code < 500, 'Server should not 500 on long text'
        data = resp.get_json()
        if data.get('success'):
            client.put(f"/api/v1/client/orders/{data['data']['id']}/cancel", headers=h)

    def test_sql_injection_in_fields(self, client):
        """SQL 注入尝试在各个字段"""
        token = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'items': [{
                'product_type_id': 1,
                'service_type_id': 15,
                'model_name': "M'; DROP TABLE orders; --",
                'brand_name': "B'; DELETE FROM customers WHERE 1=1; --",
            }],
            'delivery_type': 'store',
            'receiver_name': "'; SELECT * FROM staff; --",
            'customer_note': "' OR '1'='1",
        }, headers=h)
        assert resp.status_code < 500, 'Server should not 500 on SQL injection attempt'
        data = resp.get_json()
        if data.get('success'):
            client.put(f"/api/v1/client/orders/{data['data']['id']}/cancel", headers=h)

    def test_empty_optional_fields(self, client):
        """空字符串可选字段正常接受"""
        token = self._login(client)
        h = self._auth(token)

        resp = client.post('/api/v1/client/orders', json={
            'items': [{'product_type_id': 1, 'service_type_id': 15}],
            'delivery_type': 'store',
            'receiver_name': '',
            'receiver_phone': '',
            'customer_note': '',
        }, headers=h)
        data = resp.get_json()
        assert data['success'], f'empty optional fields should be accepted: {data}'
        client.put(f"/api/v1/client/orders/{data['data']['id']}/cancel", headers=h)

    def test_missing_body(self, client):
        """POST 空 body → 优雅处理"""
        resp = client.post('/api/v1/client/orders',
                           headers={'Content-Type': 'application/json'})
        assert resp.status_code < 500, 'Server should handle empty body gracefully'

    def test_batch_order_creation(self, client):
        """连续创建多个订单 → 均成功"""
        token = self._login(client)
        h = self._auth(token)
        oids = []

        try:
            for i in range(3):
                resp = client.post('/api/v1/client/orders', json={
                    'items': [{
                        'product_type_id': 1,
                        'service_type_id': 15,
                        'model_name': f'BatchTest-{i}',
                    }],
                    'delivery_type': 'store',
                    'customer_note': f'批量测试 #{i}',
                }, headers=h)
                data = resp.get_json()
                assert data['success'], f'batch order {i} failed: {data}'
                oids.append(data['data']['id'])

            # Verify all appear in list
            resp_list = client.get('/api/v1/client/orders/my', headers=h)
            orders = resp_list.get_json().get('data', [])
            for oid in oids:
                assert any(o['id'] == oid for o in orders), \
                    f'batch order {oid} not found in list'
        finally:
            for oid in oids:
                client.put(f'/api/v1/client/orders/{oid}/cancel', headers=h)
