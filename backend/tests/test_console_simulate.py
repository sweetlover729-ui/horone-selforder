"""Tests for routes_console/simulate.py — create, step, cleanup"""
import pytest

class TestConsoleSimulate:
    """Cover /simulate/create, /step/<step>, /cleanup"""

    def _admin_headers(self, staff_token):
        return {'X-Staff-Token': staff_token, 'Content-Type': 'application/json'}

    def test_create_success(self, client, staff_token):
        r = client.post('/api/v1/console/simulate/create',
                        headers=self._admin_headers(staff_token), json={})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert 'order_id' in d['data']

    def test_create_non_admin(self, client, tech_token):
        r = client.post('/api/v1/console/simulate/create',
                        headers={'X-Staff-Token': tech_token, 'Content-Type': 'application/json'},
                        json={})
        assert r.status_code == 403

    def test_step_unknown(self, client, staff_token):
        # 先创建订单获得真实ID，再测试未知步骤
        r = client.post('/api/v1/console/simulate/create',
                        headers=self._admin_headers(staff_token), json={})
        oid = r.get_json()['data']['order_id']
        r = client.post(f'/api/v1/console/simulate/{oid}/step/bogus',
                        headers=self._admin_headers(staff_token), json={})
        assert r.status_code == 400

    def test_step_no_auth(self, client):
        r = client.post('/api/v1/console/simulate/1/step/receive',
                        headers={'Content-Type': 'application/json'}, json={})
        assert r.status_code == 401

    def test_step_non_simu(self, client, staff_token, db_conn):
        """Step on non-simulation order → 404"""
        r = client.post('/api/v1/console/simulate/99999/step/receive',
                        headers=self._admin_headers(staff_token), json={})
        assert r.status_code == 404

    def test_full_flow_steps(self, client, staff_token):
        """Execute all 8 steps end to end"""
        r = client.post('/api/v1/console/simulate/create',
                        headers=self._admin_headers(staff_token), json={})
        assert r.status_code == 200
        oid = r.get_json()['data']['order_id']
        h = self._admin_headers(staff_token)

        # Step: pay (with delivery and items)
        r = client.post(f'/api/v1/console/simulate/{oid}/step/pay', headers=h, json={
            'delivery_type': 'express', 'product_type_id': 1, 'brand_id': 1,
            'service_type_id': 15})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # Step: receive (with express info)
        r = client.post(f'/api/v1/console/simulate/{oid}/step/receive', headers=h, json={
            'express_company': '顺丰速运', 'express_no': 'SF12345678',
            'packaging_condition': '完好'})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # Step: inspect
        r = client.post(f'/api/v1/console/simulate/{oid}/step/inspect', headers=h, json={})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # Step: repair
        r = client.post(f'/api/v1/console/simulate/{oid}/step/repair', headers=h, json={})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # Step: qc (triggers PDF)
        r = client.post(f'/api/v1/console/simulate/{oid}/step/qc', headers=h, json={})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # Step: ship (with return express)
        r = client.post(f'/api/v1/console/simulate/{oid}/step/ship', headers=h, json={
            'return_express_company': '圆通快递', 'return_express_no': 'YT98765432'})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

        # Step: complete (triggers PDF)
        r = client.post(f'/api/v1/console/simulate/{oid}/step/complete', headers=h, json={})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_step_store_delivery(self, client, staff_token):
        """pay step with store delivery type"""
        r = client.post('/api/v1/console/simulate/create',
                        headers=self._admin_headers(staff_token), json={})
        oid = r.get_json()['data']['order_id']
        h = self._admin_headers(staff_token)

        r = client.post(f'/api/v1/console/simulate/{oid}/step/pay', headers=h,
                        json={'delivery_type': 'store'})
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_cleanup_success(self, client, staff_token):
        """Cleanup removes all simulation orders"""
        r = client.post('/api/v1/console/simulate/cleanup',
                        headers=self._admin_headers(staff_token))
        assert r.status_code == 200
        assert r.get_json()['success'] is True

    def test_cleanup_no_orders(self, client, staff_token):
        """Cleanup with no sim orders → success with zero cleaned"""
        r = client.post('/api/v1/console/simulate/cleanup',
                        headers=self._admin_headers(staff_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_cleanup_non_admin(self, client, tech_token):
        r = client.post('/api/v1/console/simulate/cleanup',
                        headers={'X-Staff-Token': tech_token})
        assert r.status_code == 403
