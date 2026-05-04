"""Supplement tests for routes_console/auth.py coverage gaps"""
import pytest

class TestConsoleAuthGap:
    """Cover login error paths + full change-password endpoint"""

    def test_login_invalid_json(self, client):
        r = client.post('/api/v1/console/auth/login', json={'bad': 'field'})
        assert r.status_code == 400
        d = r.get_json()
        assert not d['success']

    def test_login_wrong_password(self, client):
        r = client.post('/api/v1/console/auth/login',
                        json={'username': 'kent', 'password': 'WRONG_PW'})
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_login_no_user(self, client):
        r = client.post('/api/v1/console/auth/login',
                        json={'username': 'ghost_user', 'password': 'x'})
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_me_no_token(self, client):
        r = client.get('/api/v1/console/auth/me')
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_change_password_empty(self, client, staff_token):
        r = client.put('/api/v1/console/auth/password',
                       headers={'X-Staff-Token': staff_token},
                       json={'old_password': '', 'new_password': ''})
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_change_password_wrong_old(self, client, staff_token):
        r = client.put('/api/v1/console/auth/password',
                       headers={'X-Staff-Token': staff_token},
                       json={'old_password': 'wrong', 'new_password': 'newpw'})
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_change_password_same(self, client, staff_token):
        """Change password to same password → success (no-op update)"""
        r = client.put('/api/v1/console/auth/password',
                       headers={'X-Staff-Token': staff_token},
                       json={'old_password': 'LILY1018@kent729',
                             'new_password': 'LILY1018@kent729'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_change_password_no_token(self, client):
        r = client.put('/api/v1/console/auth/password',
                       json={'old_password': 'x', 'new_password': 'y'})
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']
