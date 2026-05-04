"""Test client products endpoints"""
import pytest

class TestClientProducts:
    """Test /api/v1/client/products/* endpoints"""

    def test_get_product_types(self, client):
        """GET /products/types → 200 with data"""
        r = client.get('/api/v1/client/products/types')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)

    def test_get_brands_all(self, client):
        """GET /products/brands (no filter) → 200"""
        r = client.get('/api/v1/client/products/brands')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert 'data' in data

    def test_get_brands_by_type(self, client):
        """GET /products/brands?type_id=1 → filtered brands"""
        r = client.get('/api/v1/client/products/brands?type_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        # All returned brands should have product_type_id=1
        for b in data['data']:
            assert b['product_type_id'] == 1

    def test_get_categories_all(self, client):
        """GET /products/categories (no filter) → 200"""
        r = client.get('/api/v1/client/products/categories')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert 'data' in data

    def test_get_categories_by_brand(self, client):
        """GET /products/categories?brand_id=1 → 200"""
        r = client.get('/api/v1/client/products/categories?brand_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

    def test_get_categories_by_product_type(self, client):
        """GET /products/categories?product_type_id=1 → 200"""
        r = client.get('/api/v1/client/products/categories?product_type_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

    def test_get_models_all(self, client):
        """GET /products/models (no filter) → 200"""
        r = client.get('/api/v1/client/products/models')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert 'data' in data

    def test_get_models_by_brand(self, client):
        """GET /products/models?brand_id=1 → 200"""
        r = client.get('/api/v1/client/products/models?brand_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

    def test_get_models_by_category_id(self, client):
        """GET /products/models?category_id=1 → 200"""
        r = client.get('/api/v1/client/products/models?category_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

    def test_get_models_by_category_old(self, client):
        """GET /products/models?category=regulator (legacy param) → 200"""
        r = client.get('/api/v1/client/products/models?category=regulator')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

    def test_get_models_by_product_type(self, client):
        """GET /products/models?product_type_id=1 → 200"""
        r = client.get('/api/v1/client/products/models?product_type_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True

    def test_get_models_invalid_brand(self, client):
        """GET /products/models?brand_id=99999 → 200, empty list"""
        r = client.get('/api/v1/client/products/models?brand_id=99999')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['data'] == []

    def test_get_full_by_type(self, client):
        """GET /products/full?type_id=1 → 200 with brand+model tree"""
        r = client.get('/api/v1/client/products/full?type_id=1')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)
        # Each brand should have 'models' key
        if data['data']:
            assert 'models' in data['data'][0]

    def test_get_full_missing_type_id(self, client):
        """GET /products/full (no type_id) → 200, success: False"""
        r = client.get('/api/v1/client/products/full')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is False
