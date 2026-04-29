# -*- coding: utf-8 -*-
"""价格管理 (price_overrides CRUD)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime
from decimal import Decimal

@admin_required
@admin_bp.route('/prices', methods=['GET'])
def get_prices():
    """获取价格配置列表"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT po.*, po.category, pt.name as product_type_name, b.name as brand_name,
               m.name as model_name, st.name as service_type_name
        FROM price_overrides po
        LEFT JOIN product_types pt ON po.product_type_id = pt.id
        LEFT JOIN brands b ON po.brand_id = b.id
        LEFT JOIN models m ON po.model_id = m.id
        LEFT JOIN service_types st ON po.service_type_id = st.id
        ORDER BY po.created_at DESC
    ''')
    data = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/prices', methods=['POST'])
def create_price():
    """创建价格配置"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    product_type_id = data.get('product_type_id')
    brand_id = data.get('brand_id')
    category = data.get('category', '')
    model_id = data.get('model_id')
    service_type_id = data.get('service_type_id')
    price = data.get('price')
    
    if price is None:
        return jsonify({'success': False, 'message': '价格不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # Upsert: 先查询是否已存在，存在则更新，否则插入
    cursor.execute('''
        SELECT id FROM price_overrides
        WHERE product_type_id = %s AND brand_id = %s AND (model_id = %s OR (model_id IS NULL AND %s IS NULL))
          AND (service_type_id = %s OR (service_type_id IS NULL AND %s IS NULL))
    ''', (product_type_id, brand_id, model_id, model_id, service_type_id, service_type_id))
    existing = cursor.fetchone()
    if existing:
        cursor.execute('UPDATE price_overrides SET price = %s WHERE id = %s', (price, existing['id']))
        conn.commit()
        database.release_connection(conn)
        return jsonify({'success': True, 'id': existing['id'], 'updated': True})
    else:
        cursor.execute('''
            INSERT INTO price_overrides (product_type_id, brand_id, category, model_id, service_type_id, price)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (product_type_id, brand_id, category, model_id, service_type_id, price))
        new_id = cursor.fetchone()['id']
        conn.commit()
        database.release_connection(conn)
        return jsonify({'success': True, 'id': new_id, 'created': True})

@admin_required
@admin_bp.route('/prices/<int:price_id>', methods=['PUT'])
def update_price(price_id):
    """更新价格配置"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    price = data.get('price')
    
    if price is None:
        return jsonify({'success': False, 'message': '价格不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE price_overrides SET price = %s WHERE id = %s
    ''', (price, price_id))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/prices/<int:price_id>', methods=['DELETE'])
def delete_price(price_id):
    """删除价格配置"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM price_overrides WHERE id = %s', (price_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ===== 客户管理 API =====
