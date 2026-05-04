# -*- coding: utf-8 -*-
"""客户端报表 (reports overview, recent)"""
from . import client_bp
from auth import validate_customer_token
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime

@client_bp.route('/reports/overview', methods=['GET'])
def reports_overview():
    """获取个人概览统计报表(需认证)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'success': False, 'message': '未登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401
    conn = database.get_connection()
    cursor = conn.cursor()

    # 我的订单总数
    cursor.execute('SELECT COUNT(*) as total FROM orders WHERE customer_id = %s', (customer['id'],))
    total = cursor.fetchone()['total']

    # 各状态订单数
    cursor.execute('''
        SELECT status, COUNT(*) as cnt FROM orders
        WHERE customer_id = %s GROUP BY status
    ''', (customer['id'],))
    status_counts = {row['status']: row['cnt'] for row in cursor.fetchall()}

    # 今日订单（排除已删除）
    cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id = %s AND date(created_at) = CURRENT_DATE AND status != 'deleted'", (customer['id'],))
    today_count = cursor.fetchone()['count']

    # 本月订单（排���已删除）
    cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id = %s AND TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(NOW(), 'YYYY-MM') AND status != 'deleted'", (customer['id'],))
    month_count = cursor.fetchone()['count']

    # 本月收入（排除已取消和已删除）
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders WHERE customer_id = %s AND TO_CHAR(created_at, 'YYYY-MM') = TO_CHAR(NOW(), 'YYYY-MM') AND status NOT IN ('cancelled', 'deleted')", (customer['id'],))
    month_revenue = cursor.fetchone()['revenue']

    # 服务类型分布
    cursor.execute('''
        SELECT st.name, COUNT(*) as cnt, SUM(oi.item_price) as revenue
        FROM order_items oi
        JOIN service_types st ON oi.service_type_id = st.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.customer_id = %s
        GROUP BY st.name
        ORDER BY cnt DESC
    ''', (customer['id'],))
    service_stats = [{'name': r['name'], 'count': r['cnt'], 'revenue': r['revenue']} for r in cursor.fetchall()]

    database.release_connection(conn)
    return jsonify({
        'success': True,
        'data': {
            'total': total,
            'today': today_count,
            'this_month': month_count,
            'status_counts': status_counts,
            'month_revenue': month_revenue,
            'service_stats': service_stats
        }
    })

@client_bp.route('/reports/recent', methods=['GET'])
def reports_recent():
    """获取最近订单列表(需认证)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'success': False, 'message': '未登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.id, o.order_no, o.status, o.total_amount, o.created_at,
               o.receiver_name, o.receiver_phone,
               pt.name as product_name, st.name as service_name
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.id
        LEFT JOIN product_types pt ON oi.product_type_id = pt.id
        LEFT JOIN service_types st ON oi.service_type_id = st.id
        WHERE o.customer_id = %s
        ORDER BY o.created_at DESC
        LIMIT 50
    ''', (customer['id'],))
    orders = []
    seen = set()
    for row in cursor.fetchall():
        oid = row['id']
        if oid in seen:
            continue  # pragma: no cover
        seen.add(oid)
        orders.append(row)
    database.release_connection(conn)
    return jsonify({'success': True, 'data': orders})

