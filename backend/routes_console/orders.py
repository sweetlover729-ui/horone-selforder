# -*- coding: utf-8 -*-
"""Console API — Order management + payment status"""

from flask import request, jsonify
import database
import json
import os
from datetime import datetime, timedelta
from psycopg2 import sql
from logging_config import get_logger
from auth import validate_staff_token, admin_required

from . import console_bp
from . import log_status_change
from . import save_base64_image

logger = get_logger('routes_console.orders')


@console_bp.route('/orders', methods=['GET'])
def get_orders():
    """获取订单列表"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 20, type=int)
    offset = (page - 1) * size
    start_date = request.args.get('startDate', '')
    end_date = request.args.get('endDate', '')
    staff_id = request.args.get('staff_id', '', type=int) or None
    product_type_id = request.args.get('product_type_id', '', type=int) or None
    brand_id = request.args.get('brand_id', '', type=int) or None
    model_id = request.args.get('model_id', '', type=int) or None
    service_type_id = request.args.get('service_type_id', '', type=int) or None
    keyword = request.args.get('keyword', '').strip()

    conn = database.get_connection()
    cursor = conn.cursor()

    # 构建 WHERE 子句
    conditions = []
    params = []
    # 始终排除已删除订单
    if status and status == 'deleted':
        conditions.append("status = %s")
        params.append('deleted')
    else:
        conditions.append("status != %s")
        params.append('deleted')
    if status:
        if status == 'repairing':
            conditions.append("status IN (%s, %s, %s)")
            params.extend(['received', 'inspecting', 'repairing'])
        else:
            conditions.append("status = %s")
            params.append(status)
    if start_date:
        conditions.append("o.created_at >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("o.created_at <= %s")
        params.append(end_date + ' 23:59:59')
    if staff_id:
        conditions.append("o.assigned_staff_id = %s")
        params.append(staff_id)
    if keyword:
        kw = f'%{keyword}%'
        conditions.append("(o.order_no LIKE %s OR o.receiver_name LIKE %s OR o.receiver_phone LIKE %s)")
        params.extend([kw, kw, kw])
    # product_type_id / brand_id / model_id / service_type_id 通过子查询
    if product_type_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE product_type_id = %s)")
        params.append(product_type_id)
    if brand_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE brand_id = %s)")
        params.append(brand_id)
    if model_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE model_id = %s)")
        params.append(model_id)
    if service_type_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE service_type_id = %s)")
        params.append(service_type_id)

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # 获取总数
    count_sql = "SELECT COUNT(*) as count FROM orders o " + where_clause
    cursor.execute(count_sql, params)
    total = cursor.fetchone()['count']

    # 获取订单列表
    list_sql = '''
        SELECT o.*, c.nickname, c.phone as customer_phone,
               s.full_name as assigned_staff_name, s.username as assigned_staff_username
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        LEFT JOIN staff s ON o.assigned_staff_id = s.id
        ''' + where_clause + '''
        ORDER BY o.created_at DESC
        LIMIT %s OFFSET %s
    '''
    cursor.execute(list_sql, params + [size, offset])

    orders = []
    for row in cursor.fetchall():
        order = row
        # 加急服务字段
        order['urgent_service'] = bool(order.get('urgent_service', False))
        order['urgent_fee'] = float(order.get('urgent_fee', 0) or 0)
        # 接单技师信息
        order['assigned_staff_name'] = order.get('assigned_staff_name') or order.get('assigned_staff_username') or ''
        # 获取订单项
        cursor.execute('''
            SELECT oi.*, pt.name as product_type_name, b.name as brand_name,
                   m.name as model_name, st.name as service_type_name
            FROM order_items oi
            LEFT JOIN product_types pt ON oi.product_type_id = pt.id
            LEFT JOIN brands b ON oi.brand_id = b.id
            LEFT JOIN models m ON oi.model_id = m.id
            LEFT JOIN service_types st ON oi.service_type_id = st.id
            WHERE oi.order_id = %s
        ''', (order['id'],))
        order['items'] = [r for r in cursor.fetchall()]
        orders.append(order)

    database.release_connection(conn)

    return jsonify({
        'success': True,
        'orders': orders,
        'total': total,
        'page': page,
        'size': size
    })

@console_bp.route('/orders/<int:order_id>/release', methods=['POST'])
def release_order(order_id):
    """管理员强制释放订单（将已接单订单放回未接单状态）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff or staff.get('role') not in ('admin', 'super_admin'):
        return jsonify({'success': False, 'message': '仅管理员可释放订单'}), 403

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'}), 404

    # 只允许释放已分配技师的订单
    if order['assigned_staff_id'] is None:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单未分配技师，无需释放'}), 400

    # 只允许释放维修中的订单（pending/confirmed/paid/received/inspecting/repairing）
    if order['status'] not in ('pending', 'confirmed', 'paid', 'received', 'inspecting', 'repairing'):
        database.release_connection(conn)
        return jsonify({'success': False, 'message': f'订单状态为{order["status"]}，无法释放'}), 400

    cursor.execute(
        "UPDATE orders SET assigned_staff_id = NULL, updated_at = NOW() WHERE id = %s",
        (order_id,)
    )
    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '订单已释放，其他技师可重新接单'})


@console_bp.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """软删除订单（仅管理员）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff or staff.get('role') not in ('admin', 'super_admin'):
        return jsonify({'success': False, 'message': '仅管理员可删除订单'}), 403

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'}), 404

    old_status = order['status']
    # 软删除
    cursor.execute(
        "UPDATE orders SET status = 'deleted', updated_at = NOW() WHERE id = %s",
        (order_id,)
    )
    log_status_change(conn, order_id, 'status', old_status, 'deleted', staff['full_name'] or staff['username'])
    conn.commit()
    database.release_connection(conn)

    # 清理照片文件（非阻塞）
    try:
        from pdf_generator import cleanup_order_photos
        cleanup_order_photos(order_id)
    except Exception:
        pass

    return jsonify({'success': True, 'message': '订单已删除'})

@console_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    """获取订单详情"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 获取订单信息
    cursor.execute('''
        SELECT o.*, c.nickname, c.name as customer_name, c.phone as customer_phone
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        WHERE o.id = %s
    ''', (order_id,))
    order = cursor.fetchone()

    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    order_dict = order
    # 加急服务字段
    order_dict['urgent_service'] = bool(order_dict.get('urgent_service', False))
    order_dict['urgent_fee'] = float(order_dict.get('urgent_fee', 0) or 0)

    # 获取订单项
    cursor.execute('''
        SELECT oi.*, pt.name as product_type_name, b.name as brand_name,
               m.name as model_name, st.name as service_type_name
        FROM order_items oi
        LEFT JOIN product_types pt ON oi.product_type_id = pt.id
        LEFT JOIN brands b ON oi.brand_id = b.id
        LEFT JOIN models m ON oi.model_id = m.id
        LEFT JOIN service_types st ON oi.service_type_id = st.id
        WHERE oi.order_id = %s
    ''', (order_id,))
    order_dict['items'] = [r for r in cursor.fetchall()]

    # 获取追踪节点（返回所有节点，不去重，前端需要显示所有照片）
    cursor.execute('''
        SELECT *
        FROM tracking_nodes
        WHERE order_id = %s
        ORDER BY created_at ASC
    ''', (order_id,))
    all_nodes = [r for r in cursor.fetchall()]
    # paid 与 created 同一步骤，优先保留 created（过滤掉 paid）
    has_created = any(n['node_code'] == 'created' for n in all_nodes)
    if has_created:
        all_nodes = [n for n in all_nodes if n['node_code'] != 'paid']
    order_dict['tracking_nodes'] = all_nodes

    # 获取专项服务记录
    cursor.execute('''
        SELECT ssr.*, ss.name as preset_name
        FROM special_service_records ssr
        LEFT JOIN special_services ss ON ssr.special_service_id = ss.id
        WHERE ssr.order_id = %s
    ''', (order_id,))
    order_dict['special_services'] = [r for r in cursor.fetchall()]

    # PDF下载URL
    if order_dict.get('pdf_path'):
        order_dict['reportUrl'] = f'/selforder-api/console/orders/{order_id}/report-pdf'
    else:
        order_dict['reportUrl'] = None

    database.release_connection(conn)
    return jsonify({'success': True, 'data': order_dict})

@console_bp.route('/orders/<int:order_id>/payment-status', methods=['PUT'])
def update_payment_status(order_id):
    """手动设置订单支付状态（管理员）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401
    
    # 仅管理员可操作
    if staff.get('role') != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可设置支付状态'})

    data = request.get_json() or {}
    payment_status = data.get('payment_status')
    
    if payment_status not in ['unpaid', 'paid', 'refunded']:
        return jsonify({'success': False, 'message': '无效的支付状态'})

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT payment_status FROM orders WHERE id = %s', (order_id,))
        old_ps = cursor.fetchone()['payment_status'] if cursor.rowcount else None
        cursor.execute('''
            UPDATE orders
            SET payment_status = %s,
                payment_time = CASE WHEN %s = 'paid' THEN NOW() ELSE payment_time END,
                updated_at = NOW()
            WHERE id = %s
        ''', (payment_status, payment_status, order_id))

        if cursor.rowcount == 0:
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '订单不存在'})
        log_status_change(conn, order_id, 'payment_status', old_ps, payment_status, staff['full_name'] or staff['username'], 'admin')

        # 添加追踪节点记录
        status_text = {'unpaid': '未支付', 'paid': '已支付', 'refunded': '已退款'}.get(payment_status, payment_status)
        cursor.execute('''
            INSERT INTO tracking_nodes (
                order_id, node_code, node_name, description,
                staff_id, staff_name, operate_time
            ) VALUES (%s, 'payment_update', '支付状态更新', %s, %s, %s, NOW())
        ''', (order_id, f'管理员设置支付状态为：{status_text}', staff['id'], staff['full_name'] or staff['username']))

        conn.commit()
        database.release_connection(conn)

        return jsonify({'success': True, 'message': f'支付状态已更新为：{status_text}'})
    except Exception as e:
        conn.rollback()
        database.release_connection(conn)
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


