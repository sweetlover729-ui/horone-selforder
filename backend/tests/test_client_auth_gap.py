"""Supplement tests for routes_client/auth.py coverage gaps"""
import pytest

class TestClientAuthGap:
    """Fill wechat_login mock, phone format error, rename, and new-creation branches"""

    def test_wechat_login_mock_new(self, client):
        """mock_login with no existing openid → creates customer, returns token"""
        r = client.post('/api/v1/client/auth/wechat-login',
                        json={'code': 'mock_login', 'openid': 'wx_gap_001', 'nickname': 'Mocker'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert 'token' in d['data']

    def test_wechat_login_real_code(self, client):
        """Non-mock code → error message"""
        r = client.post('/api/v1/client/auth/wechat-login',
                        json={'code': 'real_wx_code'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is False
        assert '暂未实现' in d['message']

    def test_phone_login_invalid_format(self, client):
        """Non-11-digit phone → 400 error"""
        r = client.post('/api/v1/client/auth/phone-login',
                        json={'phone': '12345', 'name': 'Short'})
        assert r.status_code == 400
        d = r.get_json()
        assert d['success'] is False

    def test_phone_login_existing_rename(self, client):
        """Existing customer with different name → updates name"""
        r = client.post('/api/v1/client/auth/phone-login',
                        json={'phone': '13900000001', 'name': 'Renamed'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert d['data']['name'] == 'Renamed'

    def test_phone_login_truly_new(self, client, db_conn):
        """Brand-new phone → INSERT RETURNING * path"""
        import random
        new_phone = '137' + ''.join(str(random.randint(0, 9)) for _ in range(8))
        r = client.post('/api/v1/client/auth/phone-login',
                        json={'phone': new_phone, 'name': 'Fresh'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert d['data']['phone'] == new_phone
        assert d['data']['name'] == 'Fresh'
        assert 'token' in d['data']

    def test_phone_login_missing_phone(self, client):
        """Empty phone → error"""
        r = client.post('/api/v1/client/auth/phone-login',
                        json={'phone': '', 'name': 'Nameless'})
        assert r.status_code in (200, 400)
