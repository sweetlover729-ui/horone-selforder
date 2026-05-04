"""Tests for routes_client/client_services.py endpoints"""
import pytest

class TestClientServices:
    """GET /api/v1/client/services, /special-services, /price, /prices"""

    def test_services_all(self, client):
        r = client.get('/api/v1/client/services')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert isinstance(d['data'], list)

    def test_services_by_type(self, client):
        r = client.get('/api/v1/client/services?type_id=1')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert len(d['data']) > 0

    def test_services_by_type_and_category(self, client):
        r = client.get('/api/v1/client/services?type_id=1&category=标准')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_special_services(self, client):
        r = client.get('/api/v1/client/special-services')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert isinstance(d['data'], list)

    def test_price_full(self, client):
        r = client.get('/api/v1/client/price?product_type_id=1&brand_id=1&service_type_id=15')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert 'final_price' in d['data']

    def test_price_with_model(self, client):
        r = client.get('/api/v1/client/price?product_type_id=1&brand_id=1&model_id=79&service_type_id=15')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_price_missing_svc(self, client):
        r = client.get('/api/v1/client/price?product_type_id=1&brand_id=1')
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_price_invalid_svc(self, client):
        r = client.get('/api/v1/client/price?product_type_id=1&brand_id=1&service_type_id=99999')
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_prices_normal(self, client):
        r = client.get('/api/v1/client/prices?product_type_id=1&brand_id=1')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert isinstance(d['data'], dict)

    def test_prices_with_model(self, client):
        r = client.get('/api/v1/client/prices?product_type_id=1&brand_id=1&model_id=79')
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_prices_missing_brand(self, client):
        r = client.get('/api/v1/client/prices?product_type_id=1')
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']

    def test_prices_missing_all(self, client):
        r = client.get('/api/v1/client/prices')
        assert r.status_code == 200
        d = r.get_json()
        assert not d['success']
