# -*- coding: utf-8 -*-
"""pytest configuration and fixtures for horone.selforder tests."""
import pytest
import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app
import database
from status_log import log_status_change


@pytest.fixture(scope='session')
def db_conn():
    """Session-scoped DB connection for building test data.

    Returns a connection with RealDictCursor. Caller must commit/close."""
    conn = database.get_connection()
    yield conn
    conn.close()


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as tc:
        yield tc


@pytest.fixture
def staff_token(client):
    """Login as kent (admin) and return a valid X-Staff-Token."""
    resp = client.post('/api/v1/console/auth/login',
                       json={'username': 'kent', 'password': 'LILY1018@kent729'})
    data = resp.get_json()
    assert data['success'], f'staff login failed: {data}'
    return data['token']


@pytest.fixture
def tech_token(client):
    """Login as test (technician) and return a valid X-Staff-Token."""
    resp = client.post('/api/v1/console/auth/login',
                       json={'username': 'test', 'password': 'test123456'})
    data = resp.get_json()
    assert data['success'], f'tech login failed: {data}'
    return data['token']


@pytest.fixture
def customer_token(client):
    """Login as test customer '13900000001' via phone-login, auto-creates if needed."""
    resp = client.post('/api/v1/client/auth/phone-login',
                       json={'phone': '13900000001', 'name': '测试客户'})
    data = resp.get_json()
    if not data.get('success'):
        pytest.skip(f'customer login failed: {data}')
    token = data.get('token') or data.get('data', {}).get('token', '')
    if not token:
        pytest.skip(f'no token in customer login response: {data}')
    return f'Bearer {token}'


def _cleanup_order(conn, order_id):
    """Delete test order and its tracking nodes."""
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM tracking_nodes WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM special_service_records WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM order_items WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM status_change_log WHERE order_id = %s', (order_id,))
        cur.execute('DELETE FROM orders WHERE id = %s', (order_id,))
        conn.commit()
    except Exception:
        pass  # test cleanup is best-effort
