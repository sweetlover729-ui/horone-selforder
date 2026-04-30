# -*- coding: utf-8 -*-
"""产品目录管理 (categories, product-types, brands, models)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
import psycopg2
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime
from decimal import Decimal

@admin_required
@admin_bp.route('/categories', methods=['GET'])
def get_categories():
    """获取产品类别列表"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, description, sort_order, is_active, created_at
        FROM categories
        ORDER BY sort_order, name
    ''')
    data = [dict(row) for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/categories', methods=['POST'])
def create_category():
    """创建产品类别"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    data = request.get_json()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    sort_order = data.get('sort_order', 0)

    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})

    conn = database.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO categories (name, description, sort_order)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', (name, description, sort_order))
        new_id = cursor.fetchone()['id']
        conn.commit()
        database.release_connection(conn)
        return jsonify({'success': True, 'id': new_id})
    except psycopg2.IntegrityError:
        conn.rollback()
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '类别名称已存在'})

@admin_required
@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """更新产品类别"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()

    set_clauses = []
    params = []
    for field in ['name', 'description', 'sort_order', 'is_active']:
        if field in data:
            set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
            params.append(data[field])

    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})

    params.append(category_id)
    query = sql.SQL('UPDATE categories SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """删除产品类别"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    conn = database.get_connection()
    cursor = conn.cursor()
    # 检查是否有关联的型号
    cursor.execute('SELECT COUNT(*) as cnt FROM model_categories WHERE category_id = %s', (category_id,))
    if cursor.fetchone()['cnt'] > 0:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '该类别下有关联型号，无法删除'})

    cursor.execute('DELETE FROM categories WHERE id = %s', (category_id,))
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True})

# ========== 产品类型 CRUD ==========

@admin_required
@admin_bp.route('/product-types', methods=['GET'])
def get_product_types():
    """获取产品类型列表（级联过滤：可选 brand_id/service_type_id 约束）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    brand_id = request.args.get('brand_id', type=int) or None
    service_type_id = request.args.get('service_type_id', type=int) or None

    conn = database.get_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if brand_id:
        conditions.append("pt.id IN (SELECT b.product_type_id FROM brands b JOIN order_items oi ON oi.brand_id = b.id WHERE oi.brand_id = %s)")
        params.append(brand_id)
    if service_type_id:
        conditions.append("pt.id IN (SELECT DISTINCT b.product_type_id FROM order_items oi JOIN brands b ON oi.brand_id = b.id WHERE oi.service_type_id = %s)")
        params.append(service_type_id)
    if conditions:
        where = "WHERE " + " AND ".join(conditions)
        cursor.execute(sql.SQL('''
            SELECT DISTINCT pt.id, pt.name, pt.categories, pt.sort_order
            FROM product_types pt
            {where_part}
            ORDER BY pt.sort_order, pt.name
        ''').format(where_part=sql.SQL(where)), params)
    else:
        cursor.execute('SELECT * FROM product_types ORDER BY sort_order, name')
    data = [dict(row) for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/product-types', methods=['POST'])
def create_product_type():
    """创建产品类型"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    name = data.get('name', '')
    category = data.get('category', '')
    sort_order = data.get('sort_order', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    categories = data.get('categories', '[]')
    is_active = data.get('is_active', 1)
    cursor.execute('''
        INSERT INTO product_types (name, sort_order, categories, is_active) VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (name, sort_order, categories, is_active))
    new_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True, 'id': new_id})

@admin_required
@admin_bp.route('/product-types/<int:type_id>', methods=['PUT'])
def update_product_type(type_id):
    """更新产品类型"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    name = data.get('name', '')
    sort_order = data.get('sort_order')
    is_active = data.get('is_active')
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    if name:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('name')))
        params.append(name)
    if sort_order is not None:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('sort_order')))
        params.append(sort_order)
    if is_active is not None:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('is_active')))
        params.append(is_active)
    
    # 处理categories字段
    categories = data.get('categories')
    if categories:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('categories')))
        params.append(categories)
    
    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})
    
    params.append(type_id)
    query = sql.SQL('UPDATE product_types SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/product-types/<int:type_id>', methods=['DELETE'])
def delete_product_type(type_id):
    """删除产品类型"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM product_types WHERE id = %s', (type_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ========== 品牌 CRUD ==========

@admin_required
@admin_bp.route('/brands', methods=['GET'])
def get_brands():
    """获取品牌列表（级联过滤：可选 product_type_id/service_type_id 约束）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    product_type_id = request.args.get('product_type_id', type=int) or None
    service_type_id = request.args.get('service_type_id', type=int) or None

    conn = database.get_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if product_type_id:
        conditions.append("b.product_type_id = %s")
        params.append(product_type_id)
    if service_type_id:
        conditions.append("b.id IN (SELECT DISTINCT oi.brand_id FROM order_items oi WHERE oi.service_type_id = %s)")
        params.append(service_type_id)
    if conditions:
        where = "WHERE " + " AND ".join(conditions)
        cursor.execute(sql.SQL('''
            SELECT DISTINCT b.id, b.name, b.country, b.website, b.notes,
                   pt.name as product_type_name, pt.id as product_type_id
            FROM brands b
            LEFT JOIN product_types pt ON b.product_type_id = pt.id
            {where_part}
            ORDER BY b.name
        ''').format(where_part=sql.SQL(where)), params)
    else:
        cursor.execute('''
            SELECT b.*, pt.name as product_type_name
            FROM brands b
            LEFT JOIN product_types pt ON b.product_type_id = pt.id
            ORDER BY b.name
        ''')
    data = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/brands', methods=['POST'])
def create_brand():
    """创建品牌"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    product_type_id = data.get('product_type_id')
    name = data.get('name', '')
    country = data.get('country', '')
    website = data.get('website', '')
    notes = data.get('notes', '')
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO brands (product_type_id, name, country, website, notes, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (product_type_id, name, country, website, notes, 1))
    new_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True, 'id': new_id})

@admin_required
@admin_bp.route('/brands/<int:brand_id>', methods=['PUT'])
def update_brand(brand_id):
    """更新品牌"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    for field in ['product_type_id', 'name', 'country', 'website', 'notes', 'is_active']:
        if field in data:
            set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
            params.append(data[field])
    
    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})
    
    params.append(brand_id)
    query = sql.SQL('UPDATE brands SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/brands/<int:brand_id>', methods=['DELETE'])
def delete_brand(brand_id):
    """删除品牌"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM brands WHERE id = %s', (brand_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ========== 型号 CRUD ==========

@admin_required
@admin_bp.route('/models', methods=['GET'])
def get_models():
    """获取型号列表（级联过滤：可选 brand_id/product_type_id 约束，返回关联的类别ID列表）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    brand_id = request.args.get('brand_id', type=int) or None
    product_type_id = request.args.get('product_type_id', type=int) or None

    conn = database.get_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if brand_id:
        conditions.append("m.brand_id = %s")
        params.append(brand_id)
    if product_type_id:
        conditions.append("b.product_type_id = %s")
        params.append(product_type_id)

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    cursor.execute(sql.SQL('''
        SELECT m.id, m.name, m.brand_id, m.serial_no, m.is_active,
               b.name as brand_name, pt.name as product_type_name, pt.id as product_type_id,
               ARRAY_AGG(DISTINCT mc.category_id) FILTER (WHERE mc.category_id IS NOT NULL) as category_ids,
               ARRAY_AGG(DISTINCT c.name) FILTER (WHERE c.name IS NOT NULL) as categories
        FROM models m
        LEFT JOIN brands b ON m.brand_id = b.id
        LEFT JOIN product_types pt ON b.product_type_id = pt.id
        LEFT JOIN model_categories mc ON m.id = mc.model_id
        LEFT JOIN categories c ON mc.category_id = c.id
        {where_part}
        GROUP BY m.id, m.name, m.brand_id, m.serial_no, m.is_active, b.name, pt.name, pt.id
        ORDER BY m.name
    ''').format(where_part=sql.SQL(where)), params)

    rows = cursor.fetchall()
    data = []
    for row in rows:
        d = dict(row)
        # 清理 None 值
        d['category_ids'] = [x for x in (d.get('category_ids') or []) if x is not None]
        d['categories'] = [x for x in (d.get('categories') or []) if x is not None]
        data.append(d)

    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/models', methods=['POST'])
def create_model():
    """创建型号（支持多类型关联）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    data = request.get_json()
    brand_id = data.get('brand_id')
    name = data.get('name', '').strip()
    category_ids = data.get('category_ids', [])  # 多选类型ID列表
    serial_no = data.get('serial_no', '')

    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        # 插入型号
        cursor.execute('''
            INSERT INTO models (brand_id, name, serial_no, is_active)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        ''', (brand_id, name, serial_no, 1))
        new_id = cursor.fetchone()['id']

        # 建立类型关联
        for cat_id in category_ids:
            cursor.execute('''
                INSERT INTO model_categories (model_id, category_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            ''', (new_id, cat_id))

        conn.commit()
        database.release_connection(conn)
        return jsonify({'success': True, 'id': new_id})
    except Exception as e:
        conn.rollback()
        database.release_connection(conn)
        return jsonify({'success': False, 'message': str(e)})

@admin_required
@admin_bp.route('/models/<int:model_id>', methods=['PUT'])
def update_model(model_id):
    """更新型号（支持多类型关联更新）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        # 更新型号基本信息
        set_clauses = []
        params = []

        for field in ['brand_id', 'name', 'serial_no', 'is_active']:
            if field in data:
                set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
                params.append(data[field])

        if set_clauses:
            params.append(model_id)
            query = sql.SQL('UPDATE models SET {} WHERE id = %s').format(
                sql.SQL(', ').join(set_clauses)
            )
            cursor.execute(query, params)

        # 更新类型关联（如果传了 category_ids）
        if 'category_ids' in data:
            # 删除旧关联
            cursor.execute('DELETE FROM model_categories WHERE model_id = %s', (model_id,))
            # 建立新关联
            for cat_id in data['category_ids']:
                cursor.execute('''
                    INSERT INTO model_categories (model_id, category_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                ''', (model_id, cat_id))

        conn.commit()
        database.release_connection(conn)
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        database.release_connection(conn)
        return jsonify({'success': False, 'message': str(e)})

@admin_required
@admin_bp.route('/models/<int:model_id>', methods=['DELETE'])
def delete_model(model_id):
    """删除型号"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})

    conn = database.get_connection()
    cursor = conn.cursor()
    # 先删除关联
    cursor.execute('DELETE FROM model_categories WHERE model_id = %s', (model_id,))
    cursor.execute('DELETE FROM models WHERE id = %s', (model_id,))
    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True})

# ========== 服务类型 CRUD ==========
