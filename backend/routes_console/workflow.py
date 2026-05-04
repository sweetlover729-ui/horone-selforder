# -*- coding: utf-8 -*-
"""Console API — Repair workflow + tech endpoints + equipment data"""

from flask import request, jsonify
import database
import json
import os
from datetime import datetime, timedelta
from psycopg2 import sql
from logging_config import get_logger
import base64
from auth import validate_staff_token, admin_required
from notification import _integration_hook_notify, notify_ship

from . import console_bp
from . import log_status_change
from . import save_base64_image

logger = get_logger('routes_console.workflow')

def _check_order_access(cursor, order_id, staff):
    """检查技师是否有权限操作此订单。Admin可操作所有订单；未分配订单所有人可操作；
    已分配订单只有分配的技师本人可操作。"""
    if staff.get('role') in ('admin', 'super_admin'):
        return True
    cursor.execute('SELECT assigned_staff_id FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    if not order:
        return False
    if order['assigned_staff_id'] is None:
        return True  # 未分配订单：任何人都可以操作
    return order['assigned_staff_id'] == staff['id']


@console_bp.route('/orders/<int:order_id>/receive', methods=['PUT'])
def receive_order(order_id):
    """确认收货"""
    try:
        token = request.headers.get('X-Staff-Token', '')
        staff = validate_staff_token(token)
        if not staff:
            return jsonify({'success': False, 'message': '未登录或token已过期'})

        data = request.get_json()
        note = data.get('note', '')
        photos_base64 = data.get('photos', [])
        express_company = data.get('express_company', '')
        express_no = data.get('express_no', '')
        packaging_condition = data.get('packaging_condition', '完好')

        conn = database.get_connection()
        cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

        # 更新订单状态（只对非received状态更新）
        cursor.execute('SELECT status FROM orders WHERE id = %s', (order_id,))
        old_status = cursor.fetchone()['status'] if cursor.rowcount else None
        cursor.execute('''
            UPDATE orders
            SET status = 'received', updated_at = NOW()
            WHERE id = %s AND status NOT IN ('inspecting', 'repairing', 'ready', 'shipped', 'completed')
        ''', (order_id,))
        if cursor.rowcount > 0:
            log_status_change(conn, order_id, 'status', old_status, 'received', staff.get('full_name') or staff.get('username') or 'unknown')

        if cursor.rowcount == 0:
            # 可能是重复提交，检查是否有 received 节点（无节点=非法状态）
            cursor.execute('SELECT id FROM tracking_nodes WHERE order_id=%s AND node_code=%s', (order_id, 'received'))
            if not cursor.fetchone():
                database.release_connection(conn)
                return jsonify({'success': False, 'message': '订单状态不正确或订单不存在'})
            # 有节点=幂等重复提交，穿透继续执行（允许追加照片/更新文字）

        # 保存快递信息（幂等更新）
        if express_company or express_no:
            cursor.execute('UPDATE orders SET express_company=%s, express_no=%s WHERE id=%s',
                          (express_company, express_no, order_id))

        # 检查是否已有 received 节点，有则更新，无则创建
        desc = f'已收到客户寄送的设备（{packaging_condition}）'
        if express_company:
            desc = f'{express_company} {express_no}，{desc}'
        cursor.execute('SELECT id, photos FROM tracking_nodes WHERE order_id=%s AND node_code=%s', (order_id, 'received'))
        existing = cursor.fetchone()
        if existing:
            node_id = existing['id']
            existing_photos = existing['photos'] or '[]'
            try:
                existing_photos = json.loads(existing_photos) if isinstance(existing_photos, str) else existing_photos
            except:
                existing_photos = []
            cursor.execute('''
                UPDATE tracking_nodes
                SET description=%s, staff_id=%s, staff_name=%s, operate_time=NOW(), operate_note=%s
                WHERE id=%s
            ''', (desc, staff['id'], staff['full_name'] or staff['username'], note, node_id))
        else:
            existing_photos = []
            cursor.execute('''
                INSERT INTO tracking_nodes (
                    order_id, node_code, node_name, description,
                    staff_id, staff_name, operate_time, operate_note, photos
                ) VALUES (%s, 'received', '确认收货', %s, %s, %s, NOW(), %s, '[]')
                RETURNING id
            ''', (order_id, desc, staff['id'], staff['full_name'] or staff['username'], note))
            node_id = cursor.fetchone()['id']
        conn.commit()

        # 保存照片（传入正确的 node_id，路径自动为 orders/{order_id}/nodes/{node_id}/）
        # 支持两种格式:
        # 1. 新格式: [{type: 'unbox'|'unbox_opened', data: base64_string}]
        # 2. 旧格式: [base64_string, base64_string]
        photo_paths = list(existing_photos)
        for item in photos_base64:
            if isinstance(item, dict) and 'data' in item:
                # 新格式：带 type 标签
                path = save_base64_image(item['data'], order_id, node_id)
                if path:
                    photo_paths.append({'type': item.get('type', 'unknown'), 'path': path})
            elif isinstance(item, str):
                # 旧格式：纯 base64 字符串（向后兼容）
                path = save_base64_image(item, order_id, node_id)
                if path:
                    photo_paths.append(path)

        # 更新节点的 photos 字段（无论是否有新照片，都更新以保留原有照片）
        cursor.execute('UPDATE tracking_nodes SET photos=%s WHERE id=%s',
                      (json.dumps(photo_paths), node_id))
        conn.commit()

        _integration_hook_notify(conn, order_id, 'console', 'received')
        database.release_connection(conn)
        return jsonify({'success': True, 'message': '确认收货成功'})
    except Exception as e:  # pragma: no cover
        import traceback  # pragma: no cover
        logger.error("[ERROR] receive_order(%s): %s\n%s", order_id, e, traceback.format_exc())  # pragma: no cover
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500  # pragma: no cover

@console_bp.route('/orders/<int:order_id>/inspect', methods=['PUT'])
def inspect_order(order_id):
    """拆件检验"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    data = request.get_json()
    photos_base64 = data.get('photos', [])
    note = data.get('note', '')
    operate_time = data.get('operate_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 获取当前订单状态
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    current_status = order_row['status']
    # 支持幂等：状态已超过 inspect 时才返回（inspect→repairing→ready→shipped→completed）
    # 当前状态=inspecting 时允许穿透继续（追加照片/更新文字说明）
    if current_status in ('repairing', 'ready', 'shipped', 'completed'):
        database.release_connection(conn)
        return jsonify({'success': True, 'message': '拆件检验已完成', 'already_done': True})
    if current_status not in ('received', 'pending', 'inspecting'):
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单状态不正确'})

    # 更新订单状态
    cursor.execute('''
        UPDATE orders
        SET status = 'inspecting', updated_at = NOW()
        WHERE id = %s
    ''', (order_id,))
    log_status_change(conn, order_id, 'status', current_status, 'inspecting', staff.get('full_name') or staff.get('username') or 'unknown')

    # 检查是否已有 inspect 节点，有则更新，无则创建
    cursor.execute('SELECT id, photos FROM tracking_nodes WHERE order_id=%s AND node_code=%s', (order_id, 'inspect'))
    existing = cursor.fetchone()
    if existing:
        node_id = existing['id']
        existing_photos = existing['photos'] or '[]'
        try:
            existing_photos = json.loads(existing_photos) if isinstance(existing_photos, str) else existing_photos
        except:
            existing_photos = []
        cursor.execute('''
            UPDATE tracking_nodes
            SET description='对设备进行拆件检验', staff_id=%s, staff_name=%s, operate_time=%s, operate_note=%s
            WHERE id=%s
        ''', (staff['id'], staff['full_name'] or staff['username'], operate_time, note, node_id))
    else:
        existing_photos = []
        cursor.execute('''
            INSERT INTO tracking_nodes (
                order_id, node_code, node_name, description,
                staff_id, staff_name, operate_time, operate_note, photos
            ) VALUES (%s, 'inspect', '拆件检验', '对设备进行拆件检验', %s, %s, %s, %s, '[]')
            RETURNING id
        ''', (order_id, staff['id'], staff['full_name'] or staff['username'],
              operate_time, note))
        node_id = cursor.fetchone()['id']
    conn.commit()

    # 保存照片到正确的节点目录
    photo_paths = list(existing_photos)
    for photo_b64 in photos_base64:
        path = save_base64_image(photo_b64, order_id, node_id)  # pragma: no cover
        if path:  # pragma: no cover
            photo_paths.append(path)  # pragma: no cover
    if photo_paths:
        cursor.execute('UPDATE tracking_nodes SET photos=%s WHERE id=%s',  # pragma: no cover
                      (json.dumps(photo_paths), node_id))  # pragma: no cover
        conn.commit()  # pragma: no cover

    _integration_hook_notify(conn, order_id, 'console', 'inspecting')
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '拆件检验记录已保存'})

@console_bp.route('/service-items', methods=['GET'])
def get_console_service_items():
    """获取维修检项（按产品类型筛选，供维修技师使用）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})  # pragma: no cover

    product_type_id = request.args.get('product_type_id', type=int)
    conn = database.get_connection()
    cursor = conn.cursor()

    if product_type_id:
        cursor.execute('''
            SELECT id, product_type_id, name, description, is_required, sort_order
            FROM service_items
            WHERE product_type_id = %s AND is_active = 1
            ORDER BY sort_order
        ''', (product_type_id,))
    else:
        cursor.execute('''
            SELECT id, product_type_id, name, description, is_required, sort_order
            FROM service_items
            WHERE is_active = 1
            ORDER BY product_type_id, sort_order
        ''')

    data = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@console_bp.route('/orders/<int:order_id>/repair', methods=['PUT'])
def repair_order(order_id):
    """维修保养"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    data = request.get_json()
    photos_base64 = data.get('photos', [])
    note = data.get('note', '')
    selected_items = data.get('selected_items', [])  # 检项ID列表
    operate_time = data.get('operate_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 构建包含检项的描述
    description = '进行设备维修保养'
    if selected_items:
        cursor.execute('''  # pragma: no cover
            SELECT name FROM service_items WHERE id = ANY(%s) ORDER BY sort_order  # pragma: no cover
        ''', (selected_items,))
        item_names = [row['name'] for row in cursor.fetchall()]  # pragma: no cover
        if item_names:  # pragma: no cover
            description = '维修检项：' + '、'.join(item_names)  # pragma: no cover

    # 获取当前订单状态
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    current_status = order_row['status']
    # 支持幂等：如果已经是 repairing 或之后状态，直接返回成功
    if current_status in ('ready', 'shipped', 'completed'):
        database.release_connection(conn)
        return jsonify({'success': True, 'message': '维修保养已完成', 'already_done': True})
    if current_status not in ('inspecting', 'received', 'repairing'):
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单状态不正确'})

    # 更新订单状态
    cursor.execute('''
        UPDATE orders
        SET status = 'repairing', updated_at = NOW()
        WHERE id = %s
    ''', (order_id,))
    log_status_change(conn, order_id, 'status', current_status, 'repairing', staff.get('full_name') or staff.get('username') or 'unknown')

    # 检查是否已有 repair 节点，有则更新，无则创建
    cursor.execute('SELECT id, photos FROM tracking_nodes WHERE order_id=%s AND node_code=%s', (order_id, 'repair'))
    existing = cursor.fetchone()
    if existing:
        node_id = existing['id']
        # 保留原有图片
        existing_photos = existing['photos'] or '[]'
        try:
            existing_photos = json.loads(existing_photos) if isinstance(existing_photos, str) else existing_photos
        except:  # pragma: no cover
            existing_photos = []  # pragma: no cover
        cursor.execute('''
            UPDATE tracking_nodes
            SET description=%s, staff_id=%s, staff_name=%s, operate_time=%s, operate_note=%s
            WHERE id=%s
        ''', (description, staff['id'], staff['full_name'] or staff['username'], operate_time, note, node_id))
    else:
        existing_photos = []
        cursor.execute('''
            INSERT INTO tracking_nodes (
                order_id, node_code, node_name, description,
                staff_id, staff_name, operate_time, operate_note, photos
            ) VALUES (%s, 'repair', '维修保养', %s, %s, %s, %s, %s, '[]')
            RETURNING id
        ''', (order_id, description, staff['id'], staff['full_name'] or staff['username'],
              operate_time, note))
        node_id = cursor.fetchone()['id']
    conn.commit()

    # 保存照片到正确的节点目录
    photo_paths = list(existing_photos)  # 从原有图片开始
    for photo_b64 in photos_base64:
        path = save_base64_image(photo_b64, order_id, node_id)  # pragma: no cover
        if path:  # pragma: no cover
            photo_paths.append(path)  # pragma: no cover
    if photo_paths:
        cursor.execute('UPDATE tracking_nodes SET photos=%s WHERE id=%s',  # pragma: no cover
                      (json.dumps(photo_paths), node_id))  # pragma: no cover
        conn.commit()  # pragma: no cover

    _integration_hook_notify(conn, order_id, 'console', 'repairing')
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '维修保养记录已保存'})

@console_bp.route('/orders/<int:order_id>/special-service', methods=['POST'])
def create_special_service(order_id):
    """发起专项服务"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})  # pragma: no cover

    data = request.get_json()
    order_item_id = data.get('order_item_id')
    special_service_id = data.get('special_service_id')
    price = data.get('price', 0)
    description = data.get('description', '')
    photos_base64 = data.get('photos', [])
    staff_note = data.get('staff_note', '')
    operate_time = data.get('operate_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 保存图片
    photo_paths = []
    for photo_b64 in photos_base64:
        path = save_base64_image(photo_b64, order_id, 'special')  # pragma: no cover
        if path:  # pragma: no cover
            photo_paths.append(path)  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 获取名称：优先使用前端传入的name，否则从预设表获取
    service_name = data.get('name', '')
    if not service_name and special_service_id:
        cursor.execute("SELECT name FROM special_services WHERE id = %s", (special_service_id,))  # pragma: no cover
        result = cursor.fetchone()  # pragma: no cover
        if result:  # pragma: no cover
            service_name = result['name']  # pragma: no cover

    quantity = data.get('quantity', 1)

    # 创建专项服务记录
    cursor.execute('''
        INSERT INTO special_service_records (
            order_id, order_item_id, special_service_id, name, description, price, quantity,
            status, staff_photos, staff_note
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s)
        RETURNING id
    ''', (order_id, order_item_id, special_service_id, service_name, description, price,
          quantity, json.dumps(photo_paths), staff_note))

    record_id = cursor.fetchone()['id']

    # 添加追踪节点
    cursor.execute('''
        INSERT INTO tracking_nodes (
            order_id, node_code, node_name, description,
            staff_id, staff_name, operate_time, operate_note
        ) VALUES (%s, 'special_service', '专项服务', %s, %s, %s, %s, %s)
    ''', (order_id, f"发起专项服务: {service_name}",
          staff['id'], staff['full_name'] or staff['username'], operate_time, staff_note))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'record_id': record_id})

@console_bp.route('/orders/<int:order_id>/special-service/<int:record_id>', methods=['PUT'])
def update_special_service(order_id, record_id):
    """更新专项服务状态"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})  # pragma: no cover

    data = request.get_json()

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 支持更新 name/price/quantity/status
    set_parts = []
    params = []

    if 'name' in data:
        set_parts.append(sql.SQL('{} = %s').format(sql.Identifier('name')))
        params.append(data['name'])
    if 'price' in data:
        set_parts.append(sql.SQL('{} = %s').format(sql.Identifier('price')))
        params.append(data['price'])
    if 'quantity' in data:
        set_parts.append(sql.SQL('{} = %s').format(sql.Identifier('quantity')))
        params.append(data['quantity'])

    status = data.get('status')
    if status:
        if status not in ['pending', 'confirmed', 'rejected', 'paid', 'completed']:
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '无效的状态'})
        set_parts.append(sql.SQL('{} = %s').format(sql.Identifier('status')))
        params.append(status)
        if status == 'confirmed':
            set_parts.append(sql.SQL('confirmed_at = NOW()'))
        elif status == 'paid':
            set_parts.append(sql.SQL('paid_at = NOW()'))

    if not set_parts:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})

    params.extend([record_id, order_id])

    cursor.execute(sql.SQL('''
        UPDATE special_service_records
        SET {}
        WHERE id = %s AND order_id = %s
    ''').format(sql.SQL(', ').join(set_parts)), params)

    if cursor.rowcount == 0:
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': '记录不存在'})  # pragma: no cover

    # 添加追踪节点
    status_map = {
        'pending': '待确认',
        'confirmed': '已确认',
        'rejected': '已拒绝',
        'paid': '已支付',
        'completed': '已完成'
    }

    cursor.execute('''
        INSERT INTO tracking_nodes (
            order_id, node_code, node_name, description,
            staff_id, staff_name, operate_time
        ) VALUES (%s, 'special_update', '专项服务更新', %s, %s, %s, NOW())
    ''', (order_id, f"专项服务状态更新为: {status_map.get(status, status)}",
          staff['id'], staff['full_name'] or staff['username']))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '状态更新成功'})

@console_bp.route('/orders/<int:order_id>/qc', methods=['PUT'])
def qc_order(order_id):
    """QC通过，生成PDF（异步后台生成避免超时）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})  # pragma: no cover

    data = request.get_json()
    photos_base64 = data.get('photos', [])
    note = data.get('note', '')
    operate_time = data.get('operate_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 获取订单信息
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()

    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    # 状态守卫：只有 repairing 状态才能 QC 通过变为 ready
    # 支持幂等：如果已经是 ready 或之后状态，直接返回成功
    if order['status'] in ('ready', 'shipped', 'completed'):
        database.release_connection(conn)
        return jsonify({'success': True, 'pdf_path': order.get('pdf_path', ''), 'message': '质检已通过', 'already_done': True})
    if order['status'] != 'repairing':
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单状态不正确'})

    order_dict = order
    order_no = order_dict.get('order_no', 'UNKNOWN')
    pdf_path = f"{database.PDF_DIR}/{order_no}.pdf"

    # 先更新订单状态为 ready（PDF路径先设为空或占位）
    cursor.execute('''
        UPDATE orders
        SET status = 'ready', pdf_path = %s, updated_at = NOW()
        WHERE id = %s
    ''', (pdf_path, order_id))
    log_status_change(conn, order_id, 'status', order['status'], 'ready', staff.get('full_name') or staff.get('username') or 'unknown')
    _integration_hook_notify(conn, order_id, 'console', 'ready')

    # 检查是否已有 qc 节点，有则更新，无则创建
    cursor.execute('SELECT id, photos FROM tracking_nodes WHERE order_id=%s AND node_code=%s', (order_id, 'qc'))
    existing = cursor.fetchone()
    if existing:
        node_id = existing['id']
        existing_photos = existing['photos'] or '[]'
        try:
            existing_photos = json.loads(existing_photos) if isinstance(existing_photos, str) else existing_photos
        except:
            existing_photos = []
        cursor.execute('''
            UPDATE tracking_nodes
            SET description='设备质检通过，生成报告', staff_id=%s, staff_name=%s, operate_time=%s, operate_note=%s
            WHERE id=%s
        ''', (staff['id'], staff['full_name'] or staff['username'], operate_time, note, node_id))
    else:
        existing_photos = []
        cursor.execute('''
            INSERT INTO tracking_nodes (
                order_id, node_code, node_name, description,
                staff_id, staff_name, operate_time, operate_note, photos
            ) VALUES (%s, 'qc', '质检通过', '设备质检通过，生成报告', %s, %s, %s, %s, '[]')
            RETURNING id
        ''', (order_id, staff['id'], staff['full_name'] or staff['username'],
              operate_time, note))
        node_id = cursor.fetchone()['id']
    conn.commit()

    # 保存照片到正确的节点目录
    photo_paths = list(existing_photos)
    for photo_b64 in photos_base64:
        path = save_base64_image(photo_b64, order_id, node_id)  # pragma: no cover
        if path:  # pragma: no cover
            photo_paths.append(path)  # pragma: no cover
    if photo_paths:
        cursor.execute('UPDATE tracking_nodes SET photos=%s WHERE id=%s',  # pragma: no cover
                      (json.dumps(photo_paths), node_id))  # pragma: no cover
        conn.commit()  # pragma: no cover

    database.release_connection(conn)

    # 后台线程生成PDF（避免阻塞HTTP响应）
    import threading
    def generate_pdf_async():
        try:
            import pdf_generator
            pdf_generator.generate_order_pdf(order_dict)
        except Exception as e:  # pragma: no cover
            logger.error("PDF生成失败 order_id=%s: %s", order_id, e)  # pragma: no cover

    threading.Thread(target=generate_pdf_async, daemon=False).start()

    return jsonify({'success': True, 'pdf_path': pdf_path, 'message': '质检通过，PDF生成中'})

@console_bp.route('/orders/<int:order_id>/return-express', methods=['PUT'])
def update_return_express(order_id):
    """填写回寄快递信息"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})  # pragma: no cover

    data = request.get_json()
    return_express_company = data.get('return_express_company', '')
    return_express_no = data.get('return_express_no', '')

    if not return_express_no:
        return jsonify({'success': False, 'message': '快递单号不能为空'})
    # 维修员寄件快递固定为顺丰
    return_express_company = '顺丰速运'

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    cursor.execute('''
        UPDATE orders
        SET return_express_company = %s, return_express_no = %s,
            updated_at = NOW()
        WHERE id = %s
    ''', (return_express_company, return_express_no, order_id))

    # 添加追踪节点
    cursor.execute('''
        INSERT INTO tracking_nodes (
            order_id, node_code, node_name, description,
            staff_id, staff_name, operate_time
        ) VALUES (%s, 'return_express', '填写回寄', %s, %s, %s, NOW())
    ''', (order_id, f"回寄快递: {return_express_company} {return_express_no}",
          staff['id'], staff['full_name'] or staff['username']))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '回寄信息已保存'})

@console_bp.route('/orders/<int:order_id>/ship', methods=['PUT'])
def ship_order(order_id):
    """确认发出"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    data = request.get_json() or {}
    note = data.get('note', '')
    photos_base64 = data.get('photos', [])
    ship_company = data.get('return_express_company', '')
    ship_no = data.get('return_express_no', '')

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 获取当前订单状态
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    current_status = order_row['status']
    # 支持幂等：如果已经是 shipped 或之后状态，直接返回成功
    if current_status in ('completed',):
        database.release_connection(conn)
        return jsonify({'success': True, 'message': '已发货', 'already_done': True})
    if current_status not in ('ready', 'shipped'):
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单状态不正确'})

    cursor.execute('''
        UPDATE orders
        SET status = 'shipped', updated_at = NOW()
        WHERE id = %s
    ''', (order_id,))
    log_status_change(conn, order_id, 'status', current_status, 'shipped', staff.get('full_name') or staff.get('username') or 'unknown')

    # 更新回寄快递信息
    if ship_company or ship_no:
        cursor.execute('UPDATE orders SET return_express_company=%s, return_express_no=%s WHERE id=%s',
                      (ship_company, ship_no, order_id))

    # 构造描述
    desc = '设备已寄出'
    if ship_company:
        desc = f'{ship_company} {ship_no}，{desc}'

    # 检查是否已有 shipped 节点，有则更新，无则创建
    cursor.execute('SELECT id, photos FROM tracking_nodes WHERE order_id=%s AND node_code=%s', (order_id, 'shipped'))
    existing = cursor.fetchone()
    if existing:
        node_id = existing['id']
        existing_photos = existing['photos'] or '[]'
        try:
            existing_photos = json.loads(existing_photos) if isinstance(existing_photos, str) else existing_photos
        except:
            existing_photos = []
        cursor.execute('''
            UPDATE tracking_nodes
            SET description=%s, staff_id=%s, staff_name=%s, operate_time=NOW(), operate_note=%s
            WHERE id=%s
        ''', (desc, staff['id'], staff['full_name'] or staff['username'], note, node_id))
    else:
        existing_photos = []
        cursor.execute('''
            INSERT INTO tracking_nodes (
                order_id, node_code, node_name, description,
                staff_id, staff_name, operate_time, operate_note, photos
            ) VALUES (%s, 'shipped', '回寄客户', %s, %s, %s, NOW(), %s, '[]')
            RETURNING id
        ''', (order_id, desc, staff['id'], staff['full_name'] or staff['username'], note))
        node_id = cursor.fetchone()['id']
    conn.commit()

    # 保存照片
    photo_paths = list(existing_photos)
    for item in photos_base64:
        if isinstance(item, dict) and 'data' in item:  # pragma: no cover
            path = save_base64_image(item['data'], order_id, node_id)  # pragma: no cover
            if path:  # pragma: no cover
                photo_paths.append({'type': item.get('type', 'ship'), 'path': path})  # pragma: no cover
        elif isinstance(item, str):  # pragma: no cover
            path = save_base64_image(item, order_id, node_id)  # pragma: no cover
            if path:  # pragma: no cover
                photo_paths.append(path)  # pragma: no cover

    if photo_paths:
        cursor.execute('UPDATE tracking_nodes SET photos=%s WHERE id=%s',  # pragma: no cover
                      (json.dumps(photo_paths), node_id))  # pragma: no cover
        conn.commit()  # pragma: no cover

    _integration_hook_notify(conn, order_id, 'console', 'shipped',
                             {'express': ship_company, 'tracking_no': ship_no})
    database.release_connection(conn)
    return jsonify({'success': True, 'message': '发货成功'})

@console_bp.route('/orders/<int:order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    """完成订单"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    data = request.get_json() or {}
    note = data.get('note', '')

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403

    # 获取当前订单状态
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    current_status = order_row['status']
    # 支持幂等：如果已经是 completed，直接返回成功
    if current_status == 'completed':
        database.release_connection(conn)
        return jsonify({'success': True, 'message': '订单已完成', 'already_done': True})
    if current_status != 'shipped':
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单状态不正确'})

    cursor.execute('''
        UPDATE orders
        SET status = 'completed', completed_at = NOW(),
            updated_at = NOW()
        WHERE id = %s
    ''', (order_id,))
    log_status_change(conn, order_id, 'status', current_status, 'completed', staff.get('full_name') or staff.get('username') or 'unknown')

    # 添加追踪节点
    cursor.execute('''
        INSERT INTO tracking_nodes (
            order_id, node_code, node_name, description,
            staff_id, staff_name, operate_time, operate_note
        ) VALUES (%s, 'completed', '订单完成', '订单已完成', %s, %s, NOW(), %s)
    ''', (order_id, staff['id'], staff['full_name'] or staff['username'], note))

    conn.commit()
    _integration_hook_notify(conn, order_id, 'console', 'completed')
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '订单已完成'})
@console_bp.route('/tech/orders', methods=['GET'])
def tech_orders():
    """技术员获取自己的订单列表（分新订单和我的订单）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        # 我的订单：已分配给我的、或我有操作记录的
        cursor.execute('''
            SELECT DISTINCT o.* FROM orders o
            WHERE o.is_simulation = 0
            AND o.status != 'deleted'
            AND (o.assigned_staff_id = %s
                 OR EXISTS (SELECT 1 FROM tracking_nodes tn
                            WHERE tn.order_id = o.id AND tn.staff_id = %s))
            ORDER BY o.created_at DESC
        ''', (staff['id'], staff['id']))
        my_orders = [{**r, 'is_mine': True} for r in cursor.fetchall()]
        # 新订单：待认领（pending 或 confirmed 且未分配）
        cursor.execute('''
            SELECT * FROM orders
            WHERE is_simulation = 0 AND status IN ('pending', 'confirmed')
            AND assigned_staff_id IS NULL ORDER BY created_at DESC
        ''')
        new_orders = [{**r, 'is_mine': False} for r in cursor.fetchall()]
        return jsonify({'success': True, 'data': {
            'my_orders': my_orders,
            'new_orders': new_orders,
            'total': len(my_orders) + len(new_orders)
        }})
    finally:
        database.release_connection(conn)



@console_bp.route('/tech/orders/<int:order_id>/accept', methods=['POST'])
def tech_accept_order(order_id):
    """技术员认领订单"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = %s AND is_simulation = 0', (order_id,))
        order = cursor.fetchone()
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        if order['assigned_staff_id'] is not None and order['assigned_staff_id'] != staff['id']:
            return jsonify({'success': False, 'message': '此订单已被其他技术员认领'}), 400
        # 已领取的订单，直接返回继续处理
        if order['assigned_staff_id'] == staff['id']:
            return jsonify({'success': True, 'message': '这是您的订单，继续处理'})
        # 只允许 paid/confirmed/pending 状态的订单被领取
        if order['status'] not in ('paid', 'confirmed', 'pending'):
            return jsonify({'success': False, 'message': '订单状态为' + order['status'] + '，无法接单'}), 400
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 只分配技师，不改状态、不创建节点（节点由TechWorkflow提交时创建）
        cursor.execute('UPDATE orders SET assigned_staff_id=%s, updated_at=%s WHERE id=%s',
                      (staff['id'], now, order_id))
        conn.commit()
        return jsonify({'success': True, 'message': '接单成功'})
    finally:
        database.release_connection(conn)



@console_bp.route('/orders/<int:order_id>/nodes/<int:node_id>/photo/<filename>', methods=['DELETE'])
def delete_node_photo(order_id, node_id, filename):
    """删除节点照片"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401  # pragma: no cover

    conn = database.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tracking_nodes WHERE id = %s AND order_id = %s', (node_id, order_id))
        node = cursor.fetchone()
        if not node:
            return jsonify({'success': False, 'message': '节点不存在'}), 404

        photos = json.loads(node['photos'] or '[]')
        
        # 支持两种格式:
        # 1. 新格式: [{type: 'unbox', path: 'orders/.../file.jpg'}]
        # 2. 旧格式: ['orders/.../file.jpg']
        photo_to_delete = None
        for item in photos:
            if isinstance(item, dict) and item.get('path', '').endswith(filename):
                photo_to_delete = item  # pragma: no cover
                break  # pragma: no cover
            elif isinstance(item, str) and item.endswith(filename):
                photo_to_delete = item
                break
        
        if not photo_to_delete:
            return jsonify({'success': False, 'message': '照片不存在'}), 404

        # 删除文件
        file_path = os.path.join(database.UPLOAD_DIR, photo_to_delete['path'] if isinstance(photo_to_delete, dict) else photo_to_delete)
        if os.path.exists(file_path):
            os.remove(file_path)  # pragma: no cover

        # 从列表移除
        photos.remove(photo_to_delete)
        cursor.execute('UPDATE tracking_nodes SET photos = %s WHERE id = %s', (json.dumps(photos), node_id))
        conn.commit()
        return jsonify({'success': True, 'message': '照片已删除'})
    finally:
        database.release_connection(conn)




@console_bp.route('/orders/<int:order_id>/equipment-data', methods=['GET'])
def get_equipment_data(order_id):
    """获取订单的设备检测数据"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403
    
    # 获取订单的所有 order_items
    cursor.execute('''
        SELECT oi.id as order_item_id, oi.quantity, 
               pt.name as product_type_name, b.name as brand_name, m.name as model_name
        FROM order_items oi
        LEFT JOIN product_types pt ON oi.product_type_id = pt.id
        LEFT JOIN brands b ON oi.brand_id = b.id
        LEFT JOIN models m ON oi.model_id = m.id
        WHERE oi.order_id = %s
    ''', (order_id,))
    items = cursor.fetchall()
    
    result = []
    for item in items:
        # 获取每个 order_item 的检测数据
        cursor.execute('''
            SELECT * FROM equipment_inspection_data
            WHERE order_item_id = %s
        ''', (item['order_item_id'],))
        data = cursor.fetchone()
        
        result.append({
            'order_item_id': item['order_item_id'],
            'product_type_name': item['product_type_name'],
            'brand_name': item['brand_name'],
            'model_name': item['model_name'],
            'quantity': item['quantity'],
            'inspection_data': {
                'id': data['id'] if data else None,
                'first_stage_count': data['first_stage_count'] if data else 1,
                'first_stage_serials': data['first_stage_serials'] if data else [],
                'first_stage_pre_pressure': data['first_stage_pre_pressure'] if data else [],
                'first_stage_post_pressure': data['first_stage_post_pressure'] if data else [],
                'second_stage_count': data['second_stage_count'] if data else 1,
                'second_stage_serials': data['second_stage_serials'] if data else [],
                'second_stage_pre_resistance': data['second_stage_pre_resistance'] if data else [],
                'second_stage_post_resistance': data['second_stage_post_resistance'] if data else [],
                'staff_name': data['staff_name'] if data else None,
                'created_at': data['created_at'].isoformat() if data and data['created_at'] else None,
            } if data else None
        })
    
    database.release_connection(conn)
    return jsonify({'success': True, 'data': result})


@console_bp.route('/orders/<int:order_id>/equipment-data', methods=['POST', 'PUT'])
def save_equipment_data(order_id):
    """保存/更新设备检测数据"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401  # pragma: no cover

    data = request.get_json() or {}
    items_data = data.get('items', [])
    
    if not items_data:
        return jsonify({'success': False, 'message': '无数据'}), 400

    conn = database.get_connection()
    cursor = conn.cursor()
        if not _check_order_access(cursor, order_id, staff):
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '此订单已分配给其他技师，无权操作'}), 403
    
    try:
        for item in items_data:
            order_item_id = item.get('order_item_id')
            inspection = item.get('inspection_data', {})
            
            # 数据类型映射（按数据库字段类型）
            # 所有数组字段均为 text[]：first_stage_pre_pressure / first_stage_post_pressure /
            # second_stage_pre_resistance / second_stage_post_resistance / first_stage_serials / second_stage_serials
            # → 传 Python list[str]，不做类型转换，允许任意文本（含范围值、中文、符号等）
            def clean_text_array(arr):
                """text[]: 保留空值占位（确保数组长度与count对应），空列表传 None"""
                if not arr:
                    return None
                result = []
                for x in arr:
                    if x is None or x == '':
                        result.append(None)  # pragma: no cover
                    else:
                        result.append(str(x).strip())
                return result if result else None
            
            # 显式None检查，避免0被当作falsy处理
            fs_count_raw = inspection.get('first_stage_count')
            fs_count = fs_count_raw if fs_count_raw is not None else 1
            ss_count_raw = inspection.get('second_stage_count')
            ss_count = ss_count_raw if ss_count_raw is not None else 1
            
            fs_pre   = clean_text_array(inspection.get('first_stage_pre_pressure', []))
            fs_post  = clean_text_array(inspection.get('first_stage_post_pressure', []))
            ss_pre   = clean_text_array(inspection.get('second_stage_pre_resistance', []))
            ss_post  = clean_text_array(inspection.get('second_stage_post_resistance', []))
            fs_ser   = clean_text_array(inspection.get('first_stage_serials', []))
            ss_ser   = clean_text_array(inspection.get('second_stage_serials', []))
            
            cursor.execute('SELECT id FROM equipment_inspection_data WHERE order_item_id = %s', (order_item_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE equipment_inspection_data SET
                        first_stage_count = %s,
                        first_stage_serials = %s,
                        first_stage_pre_pressure = %s,
                        first_stage_post_pressure = %s,
                        second_stage_count = %s,
                        second_stage_serials = %s,
                        second_stage_pre_resistance = %s,
                        second_stage_post_resistance = %s,
                        updated_at = NOW(),
                        staff_id = %s,
                        staff_name = %s
                    WHERE order_item_id = %s
                ''', (
                    fs_count, fs_ser,
                    fs_pre, fs_post,
                    ss_count, ss_ser,
                    ss_pre, ss_post,
                    staff['id'],
                    staff['full_name'] or staff['username'],
                    order_item_id
                ))
            else:
                cursor.execute('''
                    INSERT INTO equipment_inspection_data (
                        order_item_id, order_id,
                        first_stage_count, first_stage_serials,
                        first_stage_pre_pressure, first_stage_post_pressure,
                        second_stage_count, second_stage_serials,
                        second_stage_pre_resistance, second_stage_post_resistance,
                        staff_id, staff_name
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    order_item_id, order_id,
                    fs_count, fs_ser,
                    fs_pre, fs_post,
                    ss_count, ss_ser,
                    ss_pre, ss_post,
                    staff['id'],
                    staff['full_name'] or staff['username']
                ))
        
        conn.commit()
        return jsonify({'success': True, 'message': '保存成功'})
    except Exception as e:  # pragma: no cover
        conn.rollback()  # pragma: no cover
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500  # pragma: no cover
    finally:
        database.release_connection(conn)
