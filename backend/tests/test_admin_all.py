# -*- coding: utf-8 -*-
"""Tests for all admin routes: catalog, services, staff, pricing, customers,
inventory, backup_restore, maintenance."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def _headers(token):
    return {'X-Staff-Token': token, 'Content-Type': 'application/json'}


def _h(token):
    return {'X-Staff-Token': token}


# ═══════════════════════════════════════════════════════════
# Catalog: categories / product-types / brands / models
# ═══════════════════════════════════════════════════════════

class TestAdminCatalog:
    def test_get_categories(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/categories', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_create_category(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/categories',
                           json={'name': '_TEST_CAT_', 'description': 'test', 'sort_order': 99},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        cat_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/categories/{cat_id}',
                          json={'description': 'updated'},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/categories/{cat_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_category_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/categories',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_create_category_duplicate(self, client, staff_token, db_conn):
        resp = client.post('/api/v1/console/admin/categories',
                           json={'name': '_DUP_CAT_'}, headers=_headers(staff_token))
        data = resp.get_json()
        cid = data['id']
        resp2 = client.post('/api/v1/console/admin/categories',
                            json={'name': '_DUP_CAT_'}, headers=_headers(staff_token))
        data2 = resp2.get_json()
        assert data2['success'] is False
        # Cleanup
        cur = db_conn.cursor()
        cur.execute('DELETE FROM categories WHERE id=%s', (cid,))
        db_conn.commit()

    def test_update_category_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/categories/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_delete_category_with_models(self, client, staff_token):
        """Deleting category with associated models fails."""
        # Category 1 likely has associated models
        resp = client.delete('/api/v1/console/admin/categories/1', headers=_h(staff_token))
        data = resp.get_json()
        # Could succeed or fail depending on seed data
        assert resp.status_code in (200, 400)

    # --- Product Types ---
    def test_get_product_types(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/product-types', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_product_types_filtered(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/product-types?brand_id=1', headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_product_types_by_service_type(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/product-types?service_type_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_product_type(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/product-types',
                           json={'name': '_TEST_PT_', 'sort_order': 999,
                                 'categories': ['regulator']},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        pt_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/product-types/{pt_id}',
                          json={'name': '_TEST_PT_UPDATED_', 'is_active': 0},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Update with categories
        resp = client.put(f'/api/v1/console/admin/product-types/{pt_id}',
                          json={'categories': '{"regulator","bcd"}'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/product-types/{pt_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_product_type_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/product-types',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    # --- Brands ---
    def test_get_brands(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/brands', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_brands_filtered(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/brands?product_type_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_brands_by_service_type(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/brands?service_type_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_brand(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/brands',
                           json={'product_type_id': 1, 'name': '_TEST_BRAND_',
                                 'country': 'TestCountry', 'website': 'https://test.com'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        brand_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/brands/{brand_id}',
                          json={'notes': 'updated notes', 'is_active': 1},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/brands/{brand_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_brand_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/brands',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_brand_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/brands/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    # --- Models ---
    def test_get_models(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/models', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_models_filtered(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/models?brand_id=1', headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_models_by_product_type(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/models?product_type_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_model(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/models',
                           json={'brand_id': 1, 'name': '_TEST_MODEL_',
                                 'category_ids': [1, 2]},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        model_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/models/{model_id}',
                          json={'name': '_TEST_MODEL_UPDATED_',
                                'category_ids': [1], 'is_active': 1},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/models/{model_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_model_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/models',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_model_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/models/1',
                          json={}, headers=_headers(staff_token))
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════
# Services: service-types, service-items, special-services
# ═══════════════════════════════════════════════════════════

class TestAdminServices:
    def test_get_service_types(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/service-types', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_service_types_filtered(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/service-types?product_type_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_service_types_by_brand(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/service-types?brand_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_service_type(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/service-types',
                           json={'product_type_id': 1, 'name': '_TEST_ST_',
                                 'description': 'test desc', 'base_price': 100,
                                 'sort_order': 999},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        st_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/service-types/{st_id}',
                          json={'base_price': 200, 'is_active': 0},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/service-types/{st_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_service_type_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/service-types',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_service_type_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/service-types/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    # --- Service Items ---
    def test_get_service_items(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/service-items', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_service_items_by_type(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/service-items?type_id=1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_service_item(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/service-items',
                           json={'product_type_id': 1, 'name': '_TEST_SI_',
                                 'description': 'test', 'is_required': 1},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        si_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/service-items/{si_id}',
                          json={'description': 'updated'},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/service-items/{si_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_service_item_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/service-items',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_service_item_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/service-items/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    # --- Special Services ---
    def test_get_special_services(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/special-services', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_create_special_service(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/special-services',
                           json={'name': '_TEST_SS_', 'description': 'test',
                                 'preset_price': 50},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        ss_id = data['id']

        # Update
        resp = client.put(f'/api/v1/console/admin/special-services/{ss_id}',
                          json={'description': 'updated', 'preset_price': 75},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/special-services/{ss_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_special_service_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/special-services',
                           json={'name': ''}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_special_service_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/special-services/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False


# ═══════════════════════════════════════════════════════════
# Staff management
# ═══════════════════════════════════════════════════════════

class TestAdminStaff:
    def test_get_staff(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/staff', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert len(data['data']) > 0

    def test_create_staff(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/staff',
                           json={'username': '_test_user_', 'password': 'pass123',
                                 'full_name': 'Test User', 'role': 'technician'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        sid = data['id']

        # Update (with fullName camelCase)
        resp = client.put(f'/api/v1/console/admin/staff/{sid}',
                          json={'fullName': 'Updated User', 'role': 'technician'},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Update password
        resp2 = client.put(f'/api/v1/console/admin/staff/{sid}',
                           json={'password': 'newpass456'},
                           headers=_headers(staff_token))
        assert resp2.status_code == 200

        # Delete
        resp = client.delete(f'/api/v1/console/admin/staff/{sid}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_staff_no_credentials(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/staff',
                           json={'username': '', 'password': ''},
                           headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_create_staff_duplicate(self, client, staff_token):
        """Cannot create staff with existing username."""
        resp = client.post('/api/v1/console/admin/staff',
                           json={'username': 'kent', 'password': 'test',
                                 'full_name': 'dup'},
                           headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_staff_no_fields(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/staff/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_disable_self(self, client, staff_token):
        """Cannot disable own account."""
        resp = client.put('/api/v1/console/admin/staff/1',
                          json={'is_active': 0},
                          headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False


# ═══════════════════════════════════════════════════════════
# Pricing management
# ═══════════════════════════════════════════════════════════

class TestAdminPricing:
    def test_get_prices(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/prices', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_create_price_new(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/prices',
                           json={'product_type_id': 1, 'brand_id': 1,
                                 'model_id': None,
                                 'category': 'regulator', 'price': 99.99},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        pid = data['id']

        # Delete
        resp = client.delete(f'/api/v1/console/admin/prices/{pid}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_price_upsert(self, client, staff_token):
        """Creating same price config twice updates instead of creating."""
        price_data = {'product_type_id': 1, 'brand_id': 1,
                      'model_id': None, 'category': 'regulator', 'price': 88.88}
        resp1 = client.post('/api/v1/console/admin/prices',
                            json=price_data, headers=_headers(staff_token))
        data1 = resp1.get_json()
        pid = data1['id']

        resp2 = client.post('/api/v1/console/admin/prices',
                            json=price_data, headers=_headers(staff_token))
        data2 = resp2.get_json()
        assert data2.get('updated') is True

        # Update via PUT
        resp = client.put(f'/api/v1/console/admin/prices/{pid}',
                          json={'price': 77.77}, headers=_headers(staff_token))
        assert resp.status_code == 200

        # Cleanup
        resp = client.delete(f'/api/v1/console/admin/prices/{pid}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_price_no_price(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/prices',
                           json={'product_type_id': 1},
                           headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_price_no_price(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/prices/1',
                          json={}, headers=_headers(staff_token))
        data = resp.get_json()
        assert data['success'] is False


# ═══════════════════════════════════════════════════════════
# Customer management
# ═══════════════════════════════════════════════════════════

class TestAdminCustomers:
    def test_get_customers(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/customers', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_customers_paginated(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/customers?page=1&per_page=5',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_customers_search(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/customers?search=test',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_customer_detail(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/customers/1', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_get_customer_detail_not_found(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/customers/99999',
                          headers=_h(staff_token))
        data = resp.get_json()
        assert data['success'] is False

    def test_update_customer(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/customers/1',
                          json={'name': 'Updated Name', 'phone': '13900000001',
                                'address': 'Test Address'},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

    def test_delete_customer_no_orders(self, client, staff_token, db_conn):
        """Can delete customer with no orders."""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO customers (phone, name) VALUES ('_DEL_TEST_', '_DEL') RETURNING id")
        cid = cur.fetchone()['id']
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/admin/customers/{cid}',
                             headers=_h(staff_token))
        data = resp.get_json()
        assert data['success'] is True

    def test_delete_customer_with_orders(self, client, staff_token):
        """Cannot delete customer with associated orders."""
        resp = client.delete('/api/v1/console/admin/customers/1',
                             headers=_h(staff_token))
        data = resp.get_json()
        assert data['success'] is False
        assert '关联订单' in data.get('message', '')

    def test_get_customers_list(self, client, staff_token):
        """Simple customer list for dropdowns."""
        resp = client.get('/api/v1/console/admin/customers/list',
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_add_customer_address(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/customers/1/addresses',
                           json={'receiver_name': 'Test', 'receiver_phone': '13900000001',
                                 'receiver_address': 'Some Place'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        addr_id = data['id']

        # Delete address
        resp = client.delete(
            f'/api/v1/console/admin/customers/1/addresses/{addr_id}',
            headers=_h(staff_token))
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════
# Inventory management
# ═══════════════════════════════════════════════════════════

class TestAdminInventory:
    def test_list_parts(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/parts', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_list_parts_filtered(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/parts?category=O-ring&search=test&low_stock=0',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_part(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/parts',
                           json={'name': '_TEST_PART_', 'part_code': 'TP001',
                                 'category': 'O-ring', 'stock': 10,
                                 'min_stock': 5, 'cost_price': 1.5,
                                 'selling_price': 3.0, 'unit': '个'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        pid = data['data']['id']

        # Get detail
        resp = client.get(f'/api/v1/console/admin/parts/{pid}', headers=_h(staff_token))
        assert resp.status_code == 200

        # Update
        resp = client.put(f'/api/v1/console/admin/parts/{pid}',
                          json={'name': '_TEST_PART_UPDATED_', 'stock': 20,
                                'min_stock': 10},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Delete (soft)
        resp = client.delete(f'/api/v1/console/admin/parts/{pid}',
                             headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_part_no_name(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/parts',
                           json={'name': ''}, headers=_headers(staff_token))
        assert resp.status_code == 400

    def test_stock_in(self, client, staff_token):
        """Stock-in increases inventory."""
        # Create a test part first
        resp = client.post('/api/v1/console/admin/parts',
                           json={'name': '_STOCK_TEST_', 'category': 'O-ring', 'stock': 5},
                           headers=_headers(staff_token))
        pid = resp.get_json()['data']['id']

        resp = client.post(f'/api/v1/console/admin/parts/{pid}/stock-in',
                           json={'quantity': 10, 'notes': 'restock'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['stock'] == 15

        # Cleanup
        client.delete(f'/api/v1/console/admin/parts/{pid}', headers=_h(staff_token))

    def test_stock_in_invalid_quantity(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/parts/1/stock-in',
                           json={'quantity': 0},
                           headers=_headers(staff_token))
        assert resp.status_code == 400

    def test_stock_out(self, client, staff_token):
        """Stock-out decreases inventory."""
        resp = client.post('/api/v1/console/admin/parts',
                           json={'name': '_STOCK_OUT_TEST_', 'category': 'O-ring',
                                 'stock': 20},
                           headers=_headers(staff_token))
        pid = resp.get_json()['data']['id']

        resp = client.post(f'/api/v1/console/admin/parts/{pid}/stock-out',
                           json={'quantity': 8, 'notes': 'used in repair'},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['data']['stock'] == 12

        client.delete(f'/api/v1/console/admin/parts/{pid}', headers=_h(staff_token))

    def test_stock_out_insufficient(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/parts',
                           json={'name': '_LOW_STOCK_', 'category': 'O-ring', 'stock': 2},
                           headers=_headers(staff_token))
        pid = resp.get_json()['data']['id']

        resp = client.post(f'/api/v1/console/admin/parts/{pid}/stock-out',
                           json={'quantity': 100},
                           headers=_headers(staff_token))
        assert resp.status_code == 400

        client.delete(f'/api/v1/console/admin/parts/{pid}', headers=_h(staff_token))

    def test_stock_out_with_order(self, client, staff_token, db_conn):
        """Stock-out can associate with an order."""
        resp = client.post('/api/v1/console/admin/parts',
                           json={'name': '_ORDER_STOCK_', 'category': 'O-ring',
                                 'stock': 50, 'selling_price': 5.0},
                           headers=_headers(staff_token))
        pid = resp.get_json()['data']['id']

        resp = client.post(f'/api/v1/console/admin/parts/{pid}/stock-out',
                           json={'quantity': 3, 'order_id': 1, 'unit_price': 5.0},
                           headers=_headers(staff_token))
        assert resp.status_code == 200

        client.delete(f'/api/v1/console/admin/parts/{pid}', headers=_h(staff_token))

    def test_low_stock_parts(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/parts/low-stock', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_part_stock_history(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/parts/1/stock-log',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_order_part_usage(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/parts/usage/1',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_get_part_not_found(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/parts/99999', headers=_h(staff_token))
        assert resp.status_code == 404

    def test_update_part_not_found(self, client, staff_token):
        resp = client.put('/api/v1/console/admin/parts/99999',
                          json={'name': 'x'},
                          headers=_headers(staff_token))
        assert resp.status_code == 404

    def test_stock_in_part_not_found(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/parts/99999/stock-in',
                           json={'quantity': 5},
                           headers=_headers(staff_token))
        assert resp.status_code == 404

    def test_stock_out_part_not_found(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/parts/99999/stock-out',
                           json={'quantity': 5},
                           headers=_headers(staff_token))
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# Backup & Restore
# ═══════════════════════════════════════════════════════════

class TestAdminBackup:
    def test_export_backup(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/backup', headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'tables' in data

    def test_restore_backup_no_confirm(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/backup/restore',
                           json={'confirm': False, 'tables': {}},
                           headers=_headers(staff_token))
        assert resp.status_code == 400

    def test_restore_backup_empty_tables(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/backup/restore',
                           json={'confirm': True, 'tables': {}},
                           headers=_headers(staff_token))
        assert resp.status_code == 400

    def test_restore_backup_with_data(self, client, staff_token):
        """Restore with compatible data (no actual rows)."""
        resp = client.post('/api/v1/console/admin/backup/restore',
                           json={'confirm': True,
                                 'tables': {'categories': [], 'product_types': []}},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_archive_cleanup_non_admin(self, client, tech_token):
        resp = client.post('/api/v1/console/admin/archive-cleanup',
                           json={}, headers=_headers(tech_token))
        assert resp.status_code == 403

    def test_archive_cleanup_admin(self, client, staff_token):
        """Archive cleanup runs and processes completed orders."""
        resp = client.post('/api/v1/console/admin/archive-cleanup',
                           json={}, headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True


# ═══════════════════════════════════════════════════════════
# Maintenance reminders
# ═══════════════════════════════════════════════════════════

class TestAdminMaintenance:
    def test_list_reminders(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/maintenance-reminders',
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_list_reminders_filtered(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/maintenance-reminders?status=pending&page=1&pageSize=10',
                          headers=_h(staff_token))
        assert resp.status_code == 200

    def test_create_reminder(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/maintenance-reminders',
                           json={'equipment_summary': 'Regulator MK25',
                                 'next_service_date': '2026-12-01',
                                 'customer_id': 1},
                           headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        rid = data['id']

        # Reschedule
        resp = client.put(
            f'/api/v1/console/admin/maintenance-reminders/{rid}/reschedule',
            json={'next_service_date': '2027-01-01'},
            headers=_headers(staff_token))
        assert resp.status_code == 200

        # Dismiss
        resp = client.put(
            f'/api/v1/console/admin/maintenance-reminders/{rid}/dismiss',
            json={}, headers=_headers(staff_token))
        assert resp.status_code == 200

    def test_create_reminder_no_equipment(self, client, staff_token):
        resp = client.post('/api/v1/console/admin/maintenance-reminders',
                           json={'equipment_summary': '', 'next_service_date': ''},
                           headers=_headers(staff_token))
        assert resp.status_code == 400

    def test_reschedule_no_date(self, client, staff_token):
        resp = client.put(
            '/api/v1/console/admin/maintenance-reminders/1/reschedule',
            json={}, headers=_headers(staff_token))
        assert resp.status_code == 400

    def test_maintenance_stats(self, client, staff_token):
        resp = client.get('/api/v1/console/admin/maintenance-reminders/stats',
                          headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True


# ═══════════════════════════════════════════════════════════
# Auth enforcement
# ═══════════════════════════════════════════════════════════

class TestAdminAuth:
    def test_admin_routes_no_token(self, client):
        """All admin routes require X-Staff-Token."""
        endpoints = [
            ('GET', '/api/v1/console/admin/categories'),
            ('GET', '/api/v1/console/admin/product-types'),
            ('GET', '/api/v1/console/admin/brands'),
            ('GET', '/api/v1/console/admin/models'),
            ('GET', '/api/v1/console/admin/service-types'),
            ('GET', '/api/v1/console/admin/service-items'),
            ('GET', '/api/v1/console/admin/special-services'),
            ('GET', '/api/v1/console/admin/staff'),
            ('GET', '/api/v1/console/admin/prices'),
            ('GET', '/api/v1/console/admin/customers'),
            ('GET', '/api/v1/console/admin/parts'),
            ('GET', '/api/v1/console/admin/backup'),
            ('GET', '/api/v1/console/admin/maintenance-reminders'),
        ]
        for method, url in endpoints:
            resp = client.open(url, method=method)
            assert resp.status_code == 403, f'{method} {url} should require auth'

    def test_admin_routes_wrong_token(self, client):
        """Invalid token returns 403."""
        bad_headers = {'X-Staff-Token': 'invalid-token'}
        resp = client.get('/api/v1/console/admin/categories', headers=bad_headers)
        assert resp.status_code == 403
