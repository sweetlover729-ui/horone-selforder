# -*- coding: utf-8 -*-
"""保养提醒管理 (maintenance-reminders CRUD + stats)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
from flask import request, jsonify


def _get_staff():
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token, allow_inactive=True)
    if not staff:
        return None
    return staff


@admin_required
@admin_bp.route('/maintenance-reminders', methods=['GET'])
def list_maintenance_reminders():
    """获取保养提醒列表"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = database.get_connection()
    cursor = conn.cursor()
    status_filter = request.args.get('status', '')
    customer_id = request.args.get('customer_id', '')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    offset = (page - 1) * page_size

    conditions = []
    params = []
    if status_filter:
        conditions.append('mr.status = %s')
        params.append(status_filter)
    if customer_id:
        conditions.append('mr.customer_id = %s')
        params.append(int(customer_id))
    where_clause = ' AND '.join(conditions) if conditions else 'TRUE'

    cursor.execute(f'''
        SELECT mr.*, c.name as customer_name, c.phone as customer_phone,
               o.order_no
        FROM maintenance_reminders mr
        LEFT JOIN customers c ON c.id = mr.customer_id
        LEFT JOIN orders o ON o.id = mr.order_id
        WHERE {where_clause}
        ORDER BY mr.next_service_date ASC
        LIMIT %s OFFSET %s
    ''', params + [page_size, offset])
    reminders = [dict(r) for r in cursor.fetchall()]

    cursor.execute(f'SELECT COUNT(*) FROM maintenance_reminders mr WHERE {where_clause}', params)
    total = cursor.fetchone()['count']

    database.release_connection(conn)
    return jsonify({'success': True, 'data': reminders, 'total': total})


@admin_required
@admin_bp.route('/maintenance-reminders', methods=['POST'])
def create_manual_reminder():
    """手动创建保养提醒"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.get_json() or {}
    equipment_summary = data.get('equipment_summary', '')
    next_service_date = data.get('next_service_date', '')
    customer_id = data.get('customer_id')

    if not equipment_summary or not next_service_date:
        return jsonify({'success': False, 'message': '设备名称和保养日期必填'}), 400

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO maintenance_reminders (customer_id, equipment_summary, next_service_date)
        VALUES (%s, %s, %s)
        RETURNING id
    ''', (customer_id, equipment_summary, next_service_date))
    rid = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True, 'message': '提醒已创建', 'id': rid})


@admin_required
@admin_bp.route('/maintenance-reminders/<int:reminder_id>/reschedule', methods=['PUT'])
def reschedule_reminder(reminder_id):
    """重新预约提醒时间"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.get_json() or {}
    new_date = data.get('next_service_date')
    if not new_date:
        return jsonify({'success': False, 'message': '请提供 next_service_date'}), 400

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE maintenance_reminders
        SET next_service_date = %s, status = 'pending', reminder_sent = FALSE,
            updated_at = NOW()
        WHERE id = %s
    ''', (new_date, reminder_id))
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True, 'message': '提醒时间已更新'})


@admin_required
@admin_bp.route('/maintenance-reminders/<int:reminder_id>/dismiss', methods=['PUT'])
def dismiss_reminder(reminder_id):
    """忽略/关闭提醒"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE maintenance_reminders
        SET status = 'dismissed', updated_at = NOW()
        WHERE id = %s
    ''', (reminder_id,))
    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True, 'message': '提醒已忽略'})


@admin_required
@admin_bp.route('/maintenance-reminders/stats', methods=['GET'])
def maintenance_stats():
    """保养提醒统计"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            COUNT(*) FILTER (WHERE status = 'pending' AND next_service_date <= NOW() + INTERVAL '30 days') as upcoming,
            COUNT(*) FILTER (WHERE status = 'pending' AND next_service_date < NOW()) as overdue_pending,
            COUNT(*) FILTER (WHERE status = 'overdue') as overdue,
            COUNT(*) FILTER (WHERE status = 'pending') as total_pending
        FROM maintenance_reminders
    ''')
    row = cursor.fetchone()
    database.release_connection(conn)
    return jsonify({'success': True, 'data': dict(row)})
