# -*- coding: utf-8 -*-
"""服务管理 (service-types, service-items, special-services)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime
from decimal import Decimal
import uuid

@admin_required
@admin_bp.route('/service-types', methods=['GET'])
def get_service_types():
    """获取服务类型列表（级联过滤：可选 product_type_id/brand_id 约束）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    product_type_id = request.args.get('product_type_id', type=int) or None
    brand_id = request.args.get('brand_id', type=int) or None

    conn = database.get_connection()
    cursor = conn.cursor()
    conditions = []
    params = []
    if product_type_id:
        conditions.append("oi.product_type_id = %s")
        params.append(product_type_id)
    if brand_id:
        conditions.append("oi.brand_id = %s")
        params.append(brand_id)
    if conditions:
        where = "WHERE " + " AND ".join(conditions)
        cursor.execute(sql.SQL('''
            SELECT DISTINCT st.id, st.name, st.description, st.base_price,
                   st.sort_order, st.category, st.category_id, st.product_type_id,
                   pt.name as product_type_name
            FROM order_items oi
            JOIN service_types st ON oi.service_type_id = st.id
            LEFT JOIN product_types pt ON st.product_type_id = pt.id
            {where_part}
            ORDER BY st.sort_order, st.name
        ''').format(where_part=sql.SQL(where)), params)
    else:
        cursor.execute('''
            SELECT st.*, st.category_id, pt.name as product_type_name
            FROM service_types st
            LEFT JOIN product_types pt ON st.product_type_id = pt.id
            ORDER BY st.sort_order
        ''')
    data = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/service-types', methods=['POST'])
def create_service_type():
    """创建服务类型"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    data = request.get_json()
    product_type_id = data.get('product_type_id')
    name = data.get('name', '')
    description = data.get('description', '')
    base_price = data.get('base_price', 0)
    sort_order = data.get('sort_order', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    category_id = data.get('category_id') or None
    
    cursor.execute('''
        INSERT INTO service_types (product_type_id, name, description, base_price, sort_order, is_active, category_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (product_type_id, name, description, base_price, sort_order, 1, category_id))
    new_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True, 'id': new_id})

@admin_required
@admin_bp.route('/service-types/<int:service_type_id>', methods=['PUT'])
def update_service_type(service_type_id):
    """更新服务类型"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    for field in ['product_type_id', 'name', 'description', 'base_price', 'sort_order', 'is_active', 'category_id']:
        if field in data:
            set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
            params.append(data[field])
    
    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})
    
    params.append(service_type_id)
    query = sql.SQL('UPDATE service_types SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/service-types/<int:service_type_id>', methods=['DELETE'])
def delete_service_type(service_type_id):
    """删除服务类型"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    conn = database.get_connection()
    cursor = conn.cursor()
    # 检查是否有关联订单项或价格配置
    cursor.execute('SELECT COUNT(*) as cnt FROM order_items WHERE service_type_id = %s', (service_type_id,))
    if cursor.fetchone()['cnt'] > 0:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '该服务类型下有订单记录，无法删除'})
    cursor.execute('DELETE FROM service_types WHERE id = %s', (service_type_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ========== 服务项目 CRUD ==========

@admin_required
@admin_bp.route('/service-items', methods=['GET'])
def get_service_items():
    """获取服务项目列表"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    type_id = request.args.get('type_id', type=int)
    conn = database.get_connection()
    cursor = conn.cursor()
    
    if type_id:
        cursor.execute('''
            SELECT si.*, pt.name as product_type_name 
            FROM service_items si
            LEFT JOIN product_types pt ON si.product_type_id = pt.id
            WHERE si.product_type_id = %s ORDER BY si.sort_order
        ''', (type_id,))
    else:
        cursor.execute('''
            SELECT si.*, pt.name as product_type_name 
            FROM service_items si
            LEFT JOIN product_types pt ON si.product_type_id = pt.id
            ORDER BY si.sort_order
        ''')
    
    data = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/service-items', methods=['POST'])
def create_service_item():
    """创建服务项目"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    data = request.get_json()
    product_type_id = data.get('product_type_id')
    name = data.get('name', '')
    description = data.get('description', '')
    is_required = data.get('is_required', 1)
    sort_order = data.get('sort_order', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO service_items (product_type_id, name, description, is_required, sort_order, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    ''', (product_type_id, name, description, is_required, sort_order, 1))
    new_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True, 'id': new_id})

@admin_required
@admin_bp.route('/service-items/<int:item_id>', methods=['PUT'])
def update_service_item(item_id):
    """更新服务项目"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    for field in ['product_type_id', 'name', 'description', 'is_required', 'sort_order', 'is_active']:
        if field in data:
            set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
            params.append(data[field])
    
    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})
    
    params.append(item_id)
    query = sql.SQL('UPDATE service_items SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/service-items/<int:item_id>', methods=['DELETE'])
def delete_service_item(item_id):
    """删除服务项目"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM service_items WHERE id = %s', (item_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ========== 专项服务 CRUD ==========

@admin_required
@admin_bp.route('/special-services', methods=['GET'])
def get_special_services():
    """获取专项服务预设列表"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM special_services ORDER BY name')
    data = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/special-services', methods=['POST'])
def create_special_service():
    """创建专项服务预设"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    data = request.get_json()
    name = data.get('name', '')
    description = data.get('description', '')
    preset_price = data.get('preset_price', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '名称不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO special_services (name, description, preset_price)
        VALUES (%s, %s, %s)
        RETURNING id
    ''', (name, description, preset_price))
    new_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True, 'id': new_id})

@admin_required
@admin_bp.route('/special-services/<int:service_id>', methods=['PUT'])
def update_special_service(service_id):
    """更新专项服务预设"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    for field in ['name', 'description', 'preset_price', 'is_active']:
        if field in data:
            set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
            params.append(data[field])
    
    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})
    
    params.append(service_id)
    query = sql.SQL('UPDATE special_services SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/special-services/<int:service_id>', methods=['DELETE'])
def delete_special_service(service_id):
    """删除专项服务预设"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM special_services WHERE id = %s', (service_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ========== 员工账号 CRUD ==========
