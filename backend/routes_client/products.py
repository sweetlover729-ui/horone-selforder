# -*- coding: utf-8 -*-
"""客户端产品浏览 (product types, brands, categories, models, full)"""
from . import client_bp
import database
from psycopg2 import sql
from flask import request, jsonify

@client_bp.route('/products/types', methods=['GET'])
def get_product_types():
    """获取产品类型列表"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, sort_order, categories FROM product_types
        WHERE is_active = 1 ORDER BY sort_order
    ''')
    types = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': types})

@client_bp.route('/products/brands', methods=['GET'])
def get_brands():
    """获取品牌列表"""
    type_id = request.args.get('type_id', type=int)
    conn = database.get_connection()
    cursor = conn.cursor()

    if type_id:
        cursor.execute('''
            SELECT id, product_type_id, name, country FROM brands
            WHERE product_type_id = %s AND is_active = 1 ORDER BY name
        ''', (type_id,))
    else:
        cursor.execute('''
            SELECT id, product_type_id, name, country FROM brands
            WHERE is_active = 1 ORDER BY name
        ''')

    brands = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': brands})

@client_bp.route('/products/categories', methods=['GET'])
def get_model_categories():
    """获取产品类别列表（从categories表读取，支持按product_type_id和brand_id过滤）"""
    brand_id = request.args.get('brand_id', type=int)
    product_type_id = request.args.get('product_type_id', type=int)

    conn = database.get_connection()
    cursor = conn.cursor()

    # 如果传了 brand_id 或 product_type_id，只返回该品牌/产品类型下型号关联的类别
    if brand_id or product_type_id:
        conditions = ['m.is_active = 1', 'c.is_active = 1']
        params = []
        if brand_id:
            conditions.append('m.brand_id = %s')
            params.append(brand_id)
        if product_type_id:
            conditions.append('m.brand_id IN (SELECT id FROM brands WHERE product_type_id = %s)')
            params.append(product_type_id)

        where_clause = ' AND '.join(conditions)
        cursor.execute(sql.SQL('''
            SELECT DISTINCT c.id, c.name, c.sort_order, COUNT(m.id) as model_count
            FROM categories c
            JOIN model_categories mc ON c.id = mc.category_id
            JOIN models m ON mc.model_id = m.id
            WHERE {where_part}
            GROUP BY c.id, c.name, c.sort_order
            ORDER BY c.sort_order, c.name
        ''').format(where_part=sql.SQL(where_clause)), params)
    else:
        # 返回全部类别
        cursor.execute('''
            SELECT id, name, sort_order, 0 as model_count
            FROM categories
            WHERE is_active = 1
            ORDER BY sort_order, name
        ''')

    categories = [{'id': row['id'], 'name': row['name'], 'model_count': row['model_count']} for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': categories})

@client_bp.route('/products/models', methods=['GET'])
def get_models():
    """获取型号列表（支持按 brand_id + category_id 过滤）"""
    brand_id = request.args.get('brand_id', type=int)
    category_id = request.args.get('category_id', type=int)  # 新参数：类型ID
    category = request.args.get('category', '')  # 兼容旧参数
    product_type_id = request.args.get('product_type_id', type=int)

    conn = database.get_connection()
    cursor = conn.cursor()

    # 使用新关联表查询
    conditions = ['m.is_active = 1']
    params = []
    joins = []

    if brand_id:
        conditions.append('m.brand_id = %s')
        params.append(brand_id)
    if category_id:
        conditions.append('mc.category_id = %s')
        params.append(category_id)
        joins.append('JOIN model_categories mc ON m.id = mc.model_id')
    elif category:
        # 兼容旧逻辑：按category名称过滤
        conditions.append('m.category = %s')
        params.append(category)
    if product_type_id:
        conditions.append('m.brand_id IN (SELECT id FROM brands WHERE product_type_id = %s)')
        params.append(product_type_id)

    join_clause = ' '.join(joins)
    where_clause = ' AND '.join(conditions)

    cursor.execute(sql.SQL('''
        SELECT DISTINCT m.id, m.brand_id, m.name, m.category
        FROM models m
        {join_part}
        WHERE {where_part}
        ORDER BY m.name
    ''').format(join_part=sql.SQL(join_clause), where_part=sql.SQL(where_clause)), tuple(params))

    models = [dict(row) for row in cursor.fetchall()]

    database.release_connection(conn)
    return jsonify({'success': True, 'data': models})

@client_bp.route('/products/full', methods=['GET'])
def get_full_products():
    """获取某类型下的品牌+型号树"""
    type_id = request.args.get('type_id', type=int)
    if not type_id:
        return jsonify({'success': False, 'message': '缺少type_id参数'})

    conn = database.get_connection()
    cursor = conn.cursor()

    # 获取品牌
    cursor.execute('''
        SELECT id, name, country FROM brands
        WHERE product_type_id = %s AND is_active = 1 ORDER BY name
    ''', (type_id,))
    brands = cursor.fetchall()

    result = []
    for brand in brands:
        brand_dict = brand
        cursor.execute('''
            SELECT id, name FROM models
            WHERE brand_id = %s AND is_active = 1 ORDER BY name
        ''', (brand['id'],))
        brand_dict['models'] = [row for row in cursor.fetchall()]
        result.append(brand_dict)

    database.release_connection(conn)
    return jsonify({'success': True, 'data': result})
