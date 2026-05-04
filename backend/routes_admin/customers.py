# -*- coding: utf-8 -*-
"""客户管理 (customers CRUD + addresses + list)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime

@admin_required
@admin_bp.route('/customers', methods=['GET'])
def get_customers():
    """获取客户列表"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()

    conn = database.get_connection()
    cursor = conn.cursor()

    where = ""
    params = []
    if search:
        where = "WHERE (c.name ILIKE %s OR c.phone ILIKE %s OR c.nickname ILIKE %s)"
        params = [f'%{search}%', f'%{search}%', f'%{search}%']

    # 总数
    cursor.execute(sql.SQL('SELECT COUNT(*) as cnt FROM customers c {}').format(
        sql.SQL(where)
    ), params)
    total = cursor.fetchone()['cnt']

    # 列表（含订单数和最近地址）
    offset = (page - 1) * per_page
    cursor.execute(sql.SQL('''
        SELECT c.id, c.nickname, c.name, c.phone, c.address,
               c.is_dealer, c.discount_rate,
               c.created_at, c.updated_at,
               (SELECT COUNT(*) FROM orders WHERE customer_id = c.id AND status != 'deleted') as order_count,
               (SELECT receiver_address FROM orders WHERE customer_id = c.id
                ORDER BY created_at DESC LIMIT 1) as last_address
        FROM customers c
        {where_clause}
        ORDER BY c.id DESC
        LIMIT %s OFFSET %s
    ''').format(where_clause=sql.SQL(where)), params + [per_page, offset])
    customers = []
    for r in cursor.fetchall():
        customers.append({
            'id': r['id'],
            'nickname': r['nickname'] or '',
            'name': r['name'] or '',
            'phone': r['phone'] or '',
            'address': r['address'] or r['last_address'] or '',
            'is_dealer': r['is_dealer'] == 1,
            'discount_rate': float(r['discount_rate'] or 100),
            'order_count': r['order_count'],
            'created_at': str(r['created_at']),
            'updated_at': str(r['updated_at']),
        })

    database.release_connection(conn)
    return jsonify({
        'success': True,
        'data': {
            'customers': customers,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })

@admin_required
@admin_bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer_detail(customer_id):
    """获取客户详情（含地址历史和订单历史）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()

    # 基本信息
    cursor.execute('SELECT * FROM customers WHERE id = %s', (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '客户不存在'})

    # 地址历史（从订单历史中提取）
    cursor.execute('''
        SELECT DISTINCT ON (receiver_name, receiver_phone, receiver_address)
               receiver_name, receiver_phone, receiver_address, created_at
        FROM orders
        WHERE customer_id = %s AND receiver_address IS NOT NULL AND receiver_address != ''
        ORDER BY receiver_name, receiver_phone, receiver_address, created_at DESC
        LIMIT 10
    ''', (customer_id,))
    address_rows = cursor.fetchall()
    addresses = [{
        'id': idx,
        'receiver_name': r['receiver_name'] or customer['name'] or '',
        'receiver_phone': r['receiver_phone'] or customer['phone'] or '',
        'receiver_address': r['receiver_address'] or '',
        'created_at': str(r['created_at']) if r.get('created_at') else ''
    } for idx, r in enumerate(address_rows)]

    # 订单历史
    cursor.execute('''
        SELECT id, order_no, status, total_amount, created_at
        FROM orders
        WHERE customer_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    ''', (customer_id,))
    orders = [{
        'id': r['id'],
        'order_no': r['order_no'],
        'status': r['status'],
        'total_amount': float(r['total_amount'] or 0),
        'created_at': str(r['created_at'])
    } for r in cursor.fetchall()]

    # 如果没有 customers.address，使用最近订单的地址
    customer_address = customer['address'] or ''
    if not customer_address and addresses:
        customer_address = addresses[0]['receiver_address']  # pragma: no cover

    database.release_connection(conn)
    return jsonify({
        'success': True,
        'data': {
            'id': customer['id'],
            'nickname': customer['nickname'] or '',
            'name': customer['name'] or '',
            'phone': customer['phone'] or '',
            'address': customer_address,
            'avatar_url': customer['avatar_url'] or '',
            'openid': customer['openid'] or '',
            'is_dealer': customer['is_dealer'] == 1,
            'discount_rate': float(customer['discount_rate'] or 100),
            'created_at': str(customer['created_at']),
            'updated_at': str(customer['updated_at']),
            'addresses': addresses,
            'orders': orders
        }
    })

@admin_required
@admin_bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    """更新客户信息"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE customers SET name = %s, phone = %s, address = %s, 
            is_dealer = %s, discount_rate = %s, updated_at = NOW()
        WHERE id = %s
    ''', (data.get('name', ''), data.get('phone', ''), data.get('address', ''), 
          data.get('is_dealer', 0), data.get('discount_rate', 100), customer_id))
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    """删除客户"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()

    # 检查是否有关联订单
    cursor.execute('SELECT COUNT(*) as cnt FROM orders WHERE customer_id = %s AND status != %s', (customer_id, 'deleted'))
    order_count = cursor.fetchone()['cnt']
    if order_count > 0:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': f'该客户有 {order_count} 个关联订单，无法删除'})

    cursor.execute('DELETE FROM customers WHERE id = %s', (customer_id,))
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/customers/<int:customer_id>/addresses', methods=['POST'])
def add_customer_address(customer_id):
    """添加客户地址"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO customer_addresses (customer_id, receiver_name, receiver_phone, receiver_address)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (customer_id, data.get('receiver_name', ''), data.get('receiver_phone', ''), data.get('receiver_address', '')))
    addr_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True, 'id': addr_id})

@admin_required
@admin_bp.route('/customers/<int:customer_id>/addresses/<int:address_id>', methods=['DELETE'])
def delete_customer_address(customer_id, address_id):
    """删除客户地址"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customer_addresses WHERE id = %s AND customer_id = %s', (address_id, customer_id))
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/customers/list', methods=['GET'])
def get_customers_list():
    """获取客户简单列表（用于下拉筛选）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, phone, nickname
        FROM customers
        ORDER BY id
    ''')
    customers = [{
        'id': r['id'],
        'name': r['name'] or r['nickname'] or f'客户{r["id"]}',
        'phone': r['phone'] or ''
    } for r in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': customers})
