# -*- coding: utf-8 -*-
"""客户端物流追踪 (tracking, return-express, checkin, nodes, photos)"""
from . import client_bp
from auth import validate_customer_token
from status_log import log_status_change
import database
from psycopg2 import sql
from flask import request, jsonify, send_file
from datetime import datetime
import json
import os

@client_bp.route('/orders/<int:order_id>/tracking', methods=['GET'])
def get_tracking(order_id):
    """获取订单追踪信息(需认证+订单归属)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not token:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 获取订单
    cursor.execute('''
        SELECT o.*, c.name as customer_name, c.phone as customer_phone
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        WHERE o.id = %s
    ''', (order_id,))
    order = cursor.fetchone()

    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})
    if str(order['customer_id']) != str(customer['id']):
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无权访问此订单'}), 403

    order_dict = {
        'id': order['id'],
        'order_no': order['order_no'],
        'status': order['status'],
        'total_amount': order['total_amount'],
        'receiver_name': order['receiver_name'],
        'receiver_phone': order['receiver_phone'] or '',
        'receiver_address': order['receiver_address'],
        'express_company': order['express_company'],
        'express_no': order['express_no'],
        'return_express_company': order['return_express_company'],
        'return_express_no': order['return_express_no'],
        'created_at': order['created_at'],
        'payment_status': order['payment_status'],
    }
    order_dict['delivery_type'] = order['delivery_type'] if 'delivery_type' in order.keys() else 'store'
    order_dict['store_checkin_at'] = order['store_checkin_at'] if 'store_checkin_at' in order.keys() else None
    order_dict['archived'] = order['archived'] if 'archived' in order.keys() else 0

    # 获取订单明细
    cursor.execute('''
        SELECT oi.*, pt.name as product_name, b.name as brand_name,
               m.name as model_name, st.name as service_name, st.base_price as item_price
        FROM order_items oi
        LEFT JOIN product_types pt ON oi.product_type_id = pt.id
        LEFT JOIN brands b ON oi.brand_id = b.id
        LEFT JOIN models m ON oi.model_id = m.id
        LEFT JOIN service_types st ON oi.service_type_id = st.id
        WHERE oi.order_id = %s
    ''', (order_id,))
    items = cursor.fetchall()

    if items:
        item = items[0]
        order_dict['product_name'] = item['product_name'] or ''
        order_dict['brand_name'] = item['brand_name'] or ''
        order_dict['model_name'] = item['model_name'] or ''
        order_dict['service_name'] = item['service_name'] or ''
        order_dict['item_price'] = item['item_price'] or 0

    # 返回完整items列表（用于编辑功能）
    items_list = []
    for r in items:
        item_dict = r
        # 自定义文字优先覆盖JOIN结果
        if item_dict.get('brand_name_text'):
            item_dict['brand_name'] = item_dict['brand_name_text']
        if item_dict.get('model_name_text'):
            item_dict['model_name'] = item_dict['model_name_text']
        if item_dict.get('service_name_text'):
            item_dict['service_name'] = item_dict['service_name_text']
        items_list.append(item_dict)
    order_dict['items'] = items_list

    # 获取追踪节点
    cursor.execute('''
        SELECT * FROM tracking_nodes WHERE order_id = %s ORDER BY created_at DESC
    ''', (order_id,))
    nodes = [r for r in cursor.fetchall()]

    # 解析photos字段
    for node in nodes:
        if node.get('photos'):
            try:
                node['photos'] = json.loads(node['photos'])
            except (json.JSONDecodeError, TypeError, ValueError):
                node['photos'] = []

    # 获取待确认专项服务
    cursor.execute('''
        SELECT * FROM special_service_records WHERE order_id = %s AND status = 'pending'
    ''', (order_id,))
    pending_ss = cursor.fetchone()

    special_service_pending = None
    if pending_ss:
        photos = []
        if pending_ss.get('staff_photos'):
            try:
                photos = json.loads(pending_ss['staff_photos'])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        special_service_pending = {
            'id': pending_ss['id'],
            'name': pending_ss['name'],
            'description': pending_ss['description'],
            'price': pending_ss['price'],
            'staff_note': pending_ss.get('staff_note', ''),
            'photos': photos,
        }

    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {
            'order': order_dict,
            'nodes': nodes,
            'special_service_pending': special_service_pending,
        }
    })


# ========== 客户填写回寄快递 ==========
@client_bp.route('/orders/<int:order_id>/return-express-client', methods=['PUT'])
def update_return_express_client(order_id):
    """客户填写回寄快递信息(需认证+订单归属)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not token:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属
    cursor.execute('SELECT id FROM orders WHERE id = %s AND customer_id = %s', (order_id, customer['id']))
    if not cursor.fetchone():
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无权操作此订单'}), 403

    data = request.get_json()
    company = data.get('return_express_company', '')
    no = data.get('return_express_no', '')

    cursor.execute('''
        UPDATE orders
        SET return_express_company = %s, return_express_no = %s, updated_at = NOW()
        WHERE id = %s AND customer_id = %s
    ''', (company, no, order_id, customer['id']))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '回寄快递已填写'})


# ========== 到店签到 ==========
@client_bp.route('/orders/<int:order_id>/checkin', methods=['POST'])
def store_checkin(order_id):
    """客户到店扫码签到"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属
    cursor.execute('SELECT id, status, delivery_type FROM orders WHERE id = %s AND customer_id = %s', (order_id, customer['id']))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})
    if str(order['customer_id']) != str(customer['id']):
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无权访问此订单'}), 403

    # 验证是到店订单且状态正确
    delivery_type = order['delivery_type'] if 'delivery_type' in order.keys() else 'store'
    if delivery_type != 'store':
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '此订单不是到店交付订单'}), 400

    if order['status'] not in ['pending', 'paid']:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': f'当前状态({order["status"]})不允许签到'}), 400

    # 更新签到时间和状态
    old_status = order['status']
    cursor.execute('''
        UPDATE orders
        SET status = 'paid', payment_status = 'paid',
            payment_time = NOW(),
            store_checkin_at = NOW(),
            updated_at = NOW()
        WHERE id = %s
    ''', (order_id,))

    log_status_change(conn, order_id, 'status', old_status, 'paid', customer['nickname'] or customer['phone'], 'client')

    # 添加追踪节点
    cursor.execute('''
        INSERT INTO tracking_nodes (order_id, node_code, node_name, description, operate_time)
        VALUES (%s, 'store_checkin', '客户已到店', '客户携带设备到店,已签到确认', NOW())
    ''', (order_id,))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '签到成功,设备已接收'})





# ========== 报表统计 ==========
@client_bp.route('/orders/<int:order_id>/tracking/nodes', methods=['GET'])
def get_tracking_nodes_only(order_id):
    """获取追踪节点列表(需认证+订单归属)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'success': False, 'message': '未登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401
    # 验证订单归属
    conn3 = database.get_connection()
    cur3 = conn3.cursor()
    cur3.execute('SELECT customer_id FROM orders WHERE id = %s', (order_id,))
    order = cur3.fetchone()
    database.release_connection(conn3)
    if not order or order['customer_id'] != customer['id']:
        return jsonify({'success': False, 'message': '无权访问此订单'}), 403
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, node_code, node_name, description, operate_time
        FROM tracking_nodes
        WHERE order_id = %s ORDER BY created_at
    ''', (order_id,))
    nodes = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': nodes})

@client_bp.route('/orders/<int:order_id>/tracking/node/<node_id>', methods=['PUT'])
def update_tracking_node(order_id, node_id):
    """更新追踪节点状态(需认证+订单归属)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'success': False, 'message': '未登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401
    # 验证订单归属
    conn_check = database.get_connection()
    cur_check = conn_check.cursor()
    cur_check.execute('SELECT customer_id FROM orders WHERE id = %s', (order_id,))
    order = cur_check.fetchone()
    database.release_connection(conn_check)
    if not order or order['customer_id'] != customer['id']:
        return jsonify({'success': False, 'message': '无权操作此订单'}), 403

    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()

    set_clauses = []
    params = []

    if 'description' in data:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('description')))
        params.append(data['description'])
    if 'operate_time' in data:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('operate_time')))
        params.append(data['operate_time'])

    if set_clauses:
        params.extend([node_id, order_id])
        query = sql.SQL('UPDATE tracking_nodes SET {} WHERE id = %s AND order_id = %s').format(
            sql.SQL(', ').join(set_clauses)
        )
        cursor.execute(query, params)
        conn.commit()

    database.release_connection(conn)
    return jsonify({'success': True})

# ========== 客户查看节点照片 ==========

@client_bp.route('/orders/<int:order_id>/nodes/<int:node_id>/photo/<filename>', methods=['GET'])
def client_get_node_photo(order_id, node_id, filename):
    """客户获取节点照片"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
    if not token:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401

    # 验证订单归属
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT customer_id FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    database.release_connection(conn)
    if not order or order['customer_id'] != customer['id']:
        return jsonify({'success': False, 'message': '无权访问'}), 403

    filepath = f'{database.ORDER_UPLOAD_DIR}/{order_id}/nodes/{node_id}/{filename}'
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '照片不存在'}), 404

    return send_file(filepath)

# ========== 客户PDF下载(已合并到download_pdf函数,支持query token) ==========
