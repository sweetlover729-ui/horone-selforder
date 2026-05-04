"""Tests for routes_client/client_reports.py (overview + recent)"""
import pytest

def _auth_headers(customer_token):
    return {'Authorization': f'Bearer {customer_token}'}

class TestClientReports:
    """GET /api/v1/client/reports/overview and /recent"""

    def test_overview_with_auth(self, client, customer_token):
        r = client.get('/api/v1/client/reports/overview',
                       headers=_auth_headers(customer_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert 'total' in d['data']

    def test_recent_with_auth(self, client, customer_token):
        r = client.get('/api/v1/client/reports/recent',
                       headers=_auth_headers(customer_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert isinstance(d['data'], list)

    def test_overview_no_auth(self, client):
        r = client.get('/api/v1/client/reports/overview')
        assert r.status_code == 401
        d = r.get_json()
        assert not d['success']

    def test_recent_no_auth(self, client):
        r = client.get('/api/v1/client/reports/recent')
        assert r.status_code == 401
        d = r.get_json()
        assert not d['success']

    def test_overview_bad_token(self, client):
        r = client.get('/api/v1/client/reports/overview',
                       headers={'Authorization': 'Bearer invalid_token_xyz'})
        assert r.status_code == 401
        d = r.get_json()
        assert not d['success']

    def test_recent_bad_token(self, client):
        r = client.get('/api/v1/client/reports/recent',
                       headers={'Authorization': 'Bearer invalid_token_xyz'})
        assert r.status_code == 401
        d = r.get_json()
        assert not d['success']
