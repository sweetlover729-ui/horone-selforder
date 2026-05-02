# -*- coding: utf-8 -*-
"""catalog.py 专项测试 — 补齐未覆盖路径"""
import pytest
import uuid


def _headers(token):
    return {'X-Staff-Token': token, 'Content-Type': 'application/json'}

def _h(token):
    return {'X-Staff-Token': token}


class TestCatalogGap:
    """补齐 catalog.py 中非死代码的未覆盖路径"""

    # ===== Categories =====
    def test_delete_category_success(self, client, staff_token, db_conn):
        """删除没有关联型号的类别 → 成功路径"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO categories (name, description, sort_order) VALUES (%s, %s, %s) RETURNING id",
                    ('_DELCAT_', 'test', 9999))
        cat_id = cur.fetchone()['id']
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/admin/categories/{cat_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

        # Verify gone
        cur.execute('SELECT COUNT(*) as cnt FROM categories WHERE id=%s', (cat_id,))
        assert cur.fetchone()['cnt'] == 0

    # ===== Product Types =====
    def test_delete_product_type_success(self, client, staff_token, db_conn):
        """独立删除产品类型"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO product_types (name, sort_order, categories, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
                    ('_DELPT_', 9999, '{}', 1))
        pt_id = cur.fetchone()['id']
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/admin/product-types/{pt_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_update_product_type_with_categories(self, client, staff_token, db_conn):
        """更新产品类型含 categories 字段"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO product_types (name, sort_order, categories, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
                    ('_UPDCAT_PT_', 9998, '{}', 1))
        pt_id = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'/api/v1/console/admin/product-types/{pt_id}',
                          json={'categories': '{"regulator","bcd","octopus"}', 'is_active': 1},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Cleanup
        cur.execute('DELETE FROM product_types WHERE id=%s', (pt_id,))
        db_conn.commit()

    # ===== Brands =====
    def test_delete_brand_success(self, client, staff_token, db_conn):
        """独立删除品牌"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO brands (product_type_id, name, country, is_active) VALUES (%s, %s, %s, %s) RETURNING id",
                    (1, '_DELBRAND_', 'Test', 1))
        brand_id = cur.fetchone()['id']
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/admin/brands/{brand_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_update_brand_full(self, client, staff_token, db_conn):
        """全字段更新品牌"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO brands (product_type_id, name, country, website, notes, is_active) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                    (1, '_UPDBRAND_', 'Brazil', 'https://brazil.dive', 'initial', 1))
        brand_id = cur.fetchone()['id']
        db_conn.commit()

        resp = client.put(f'/api/v1/console/admin/brands/{brand_id}',
                          json={'product_type_id': 2, 'name': '_UPDBRAND_V2_',
                                'country': 'Chile', 'website': 'https://chile.dive',
                                'notes': 'updated all', 'is_active': 0},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Cleanup
        cur.execute('DELETE FROM brands WHERE id=%s', (brand_id,))
        db_conn.commit()

    # ===== Models =====
    def test_delete_model_success(self, client, staff_token, db_conn):
        """独立删除型号（含 model_categories 清理）"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO models (brand_id, name, serial_no, is_active) VALUES (%s,%s,%s,%s) RETURNING id",
                    (1, '_DELMODEL_', 'SN-DEL-001', 1))
        model_id = cur.fetchone()['id']
        # Add some categories to test cascade cleanup
        cur.execute("INSERT INTO model_categories (model_id, category_id) VALUES (%s,%s)", (model_id, 2))
        cur.execute("INSERT INTO model_categories (model_id, category_id) VALUES (%s,%s)", (model_id, 3))
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/admin/models/{model_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

        # Verify model_categories cleaned
        cur.execute('SELECT COUNT(*) as cnt FROM model_categories WHERE model_id=%s', (model_id,))
        assert cur.fetchone()['cnt'] == 0

    def test_update_model_full(self, client, staff_token, db_conn):
        """全字段更新型号 + category_ids 替换"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO models (brand_id, name, serial_no, is_active) VALUES (%s,%s,%s,%s) RETURNING id",
                    (1, '_UPDMODEL_', 'SN-UPD-001', 1))
        model_id = cur.fetchone()['id']
        # Seed one category
        cur.execute("INSERT INTO model_categories (model_id, category_id) VALUES (%s,%s)", (model_id, 2))
        db_conn.commit()

        resp = client.put(f'/api/v1/console/admin/models/{model_id}',
                          json={'brand_id': 2, 'name': '_UPDMODEL_V2_',
                                'serial_no': 'SN-UPD-002', 'is_active': 1,
                                'category_ids': [3, 4, 5]},
                          headers=_headers(staff_token))
        assert resp.status_code == 200

        # Verify category_ids were replaced
        cur.execute('SELECT ARRAY_AGG(category_id ORDER BY category_id) as cats FROM model_categories WHERE model_id=%s',
                    (model_id,))
        cats = cur.fetchone()['cats']
        assert sorted(cats) == [3, 4, 5]

        # Cleanup
        cur.execute('DELETE FROM model_categories WHERE model_id=%s', (model_id,))
        cur.execute('DELETE FROM models WHERE id=%s', (model_id,))
        db_conn.commit()

    def test_create_model_exception(self, client, staff_token, db_conn):
        """触发 create_model 的 except 分支（如无效 category_id）"""
        # categories.id=99999 doesn't exist, FK violation should trigger except
        resp = client.post('/api/v1/console/admin/models',
                           json={'brand_id': 1, 'name': '_ERRMODEL_',
                                 'category_ids': [99999]},
                           headers=_headers(staff_token))
        data = resp.get_json()
        # Should fail — either 200 with success=False, or an error status
        assert data.get('success') is False or resp.status_code >= 400

    def test_update_model_exception(self, client, staff_token, db_conn):
        """触发 update_model 的 except 分支"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO models (brand_id, name, serial_no, is_active) VALUES (%s,%s,%s,%s) RETURNING id",
                    (1, '_ERR_UPDMODEL_', 'SN-ERR-001', 1))
        model_id = cur.fetchone()['id']
        db_conn.commit()

        # Try update with invalid category_id that violates FK
        resp = client.put(f'/api/v1/console/admin/models/{model_id}',
                          json={'category_ids': [99999]},
                          headers=_headers(staff_token))
        data = resp.get_json()
        # Should fail
        assert data.get('success') is False or resp.status_code >= 400

        # Cleanup
        cur.execute('DELETE FROM model_categories WHERE model_id=%s', (model_id,))
        cur.execute('DELETE FROM models WHERE id=%s', (model_id,))
        db_conn.commit()

    def test_delete_category_with_models_fails(self, client, staff_token, db_conn):
        """删除有关联型号的类别 → 被拒绝"""
        cur = db_conn.cursor()
        # 创建类别
        cur.execute("INSERT INTO categories (name, description, sort_order) VALUES (%s, %s, %s) RETURNING id",
                    ('_DELCAT_LINKED_', 'has models', 9998))
        cat_id = cur.fetchone()['id']
        db_conn.commit()

        # 创建型号并关联到该类别
        cur.execute("INSERT INTO models (brand_id, name, serial_no, is_active) VALUES (%s,%s,%s,%s) RETURNING id",
                    (1, '_MODEL_FOR_CAT_', 'SN-CAT-001', 1))
        model_id = cur.fetchone()['id']
        cur.execute("INSERT INTO model_categories (model_id, category_id) VALUES (%s,%s)", (model_id, cat_id))
        db_conn.commit()

        resp = client.delete(f'/api/v1/console/admin/categories/{cat_id}',
                             headers=_h(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False
        assert '无法删除' in data['message']

        # Cleanup
        cur.execute('DELETE FROM model_categories WHERE model_id=%s', (model_id,))
        cur.execute('DELETE FROM models WHERE id=%s', (model_id,))
        cur.execute('DELETE FROM categories WHERE id=%s', (cat_id,))
        db_conn.commit()

    def test_update_product_type_empty(self, client, staff_token, db_conn):
        """更新产品类型无有效字段 → 无更新内容"""
        cur = db_conn.cursor()
        cur.execute("INSERT INTO product_types (name, sort_order, categories, is_active) VALUES (%s,%s,%s,%s) RETURNING id",
                    ('_EMPTYUPD_PT_', 9995, '{}', 1))
        pt_id = cur.fetchone()['id']
        db_conn.commit()

        # 发送空 JSON（无任何有效字段）
        resp = client.put(f'/api/v1/console/admin/product-types/{pt_id}',
                          json={},
                          headers=_headers(staff_token))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is False
        assert '无更新内容' in data['message']

        # Cleanup
        cur.execute('DELETE FROM product_types WHERE id=%s', (pt_id,))
        db_conn.commit()

    # ===== Token / Permission tests =====
    def test_catalog_no_token(self, client):
        """无 token 访问 catalog 端点 → 403（before_request 拦截）"""
        endpoints = [
            ('GET', '/api/v1/console/admin/categories'),
            ('GET', '/api/v1/console/admin/product-types'),
            ('GET', '/api/v1/console/admin/brands'),
            ('GET', '/api/v1/console/admin/models'),
        ]
        for method, url in endpoints:
            resp = client.open(url, method=method)
            assert resp.status_code == 403, f'{method} {url} should 403, got {resp.status_code}'

    def test_catalog_non_admin(self, client, tech_token):
        """技师（非管理员）无法访问 catalog 端点"""
        endpoints = [
            ('GET', '/api/v1/console/admin/categories'),
            ('POST', '/api/v1/console/admin/categories'),
            ('PUT', '/api/v1/console/admin/categories/1'),
            ('DELETE', '/api/v1/console/admin/categories/1'),
        ]
        for method, url in endpoints:
            resp = client.open(url, method=method, headers=_h(tech_token))
            assert resp.status_code == 403, f'{method} {url} should 403 for tech, got {resp.status_code}'
