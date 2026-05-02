# -*- coding: utf-8 -*-
"""Console API — Simulated order workflow"""

from flask import request, jsonify
import database
import json
import os
from datetime import datetime, timedelta
from psycopg2 import sql
from logging_config import get_logger
import secrets
from auth import validate_staff_token, admin_required
from pdf_generator import generate_order_pdf

from . import console_bp
from . import log_status_change

logger = get_logger('routes_console.simulate')


@console_bp.route('/simulate/create', methods=['POST'])
def simulate_create_order():
    """创建模拟订单"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff or staff['role'] not in ('admin', 'technician'):
        return jsonify({'success': False, 'message': '仅管理员可模拟'}), 403

    data = request.get_json() or {}
    conn = database.get_connection()
    cursor = conn.cursor()

    # 创建模拟客户
    cursor.execute("""
        INSERT INTO customers (openid, nickname, name, phone, address)
        VALUES ('sim_' || %s, '模拟客户', '模拟客户', '00000000000', '模拟地址')
        RETURNING id
    """, (secrets.token_hex(4),))
    customer_id = cursor.fetchone()['id']

    # 创建模拟订单
    import time
    order_no = f"SIM-{time.strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"
    cursor.execute("INSERT INTO orders (order_no, customer_id, status, payment_status, total_amount, delivery_type, is_simulation, receiver_name, receiver_phone, receiver_address, created_at, updated_at) VALUES (%s, %s, 'confirmed', 'paid', 200, 'express', 1, '模拟客户', '13800138000', '模拟广州市天河区', NOW(), NOW()) RETURNING id", (order_no, customer_id))
    order_id = cursor.fetchone()['id']

    # 创建初始tracking node
    cursor.execute("""
        INSERT INTO tracking_nodes (order_id, node_code, node_name, description, operate_time, created_at)
        VALUES (%s, 'created', '订单确认', '模拟客户提交订单',
                NOW(), NOW())
    """, (order_id,))

    conn.commit()
    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {'order_id': order_id, 'order_no': order_no, 'customer_id': customer_id}
    })

@console_bp.route('/simulate/<int:order_id>/step/<step>', methods=['POST'])
def simulate_step(order_id, step):
    """执行模拟流程步骤"""
    token = request.headers.get('X-Staff-Token', '') or request.args.get('token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM orders WHERE id = %s AND is_simulation = 1', (order_id,))
        order = cursor.fetchone()
        if not order:
            return {'success': False, 'message': '模拟订单不存在'}, 404

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        staff_name = staff.get('full_name') or staff.get('username', '管理员')
        sample_photo = os.path.join(database.UPLOAD_DIR, 'test', 'sample_photo.jpg')
        photo_dir = f'{database.ORDER_UPLOAD_DIR}/{order_id}'
        # 统一获取请求体（所有步骤都用到）
        item_data = request.get_json() or {}

        steps_map = {
            'create': {'status': 'confirmed', 'node_code': 'payment_update',
                       'node_name': '订单确认',
                       'description': '订单确认'},
            'pay':    {'status': 'confirmed', 'node_code': 'payment_update',
                       'node_name': '订单确认',
                       'description': '确认收货'},
            'receive':{'status': 'received', 'node_code': 'received',
                       'node_name': '确认收货',
                       'description': '拆开邮包后拍照记录包装状态'},
            'inspect':{'status': 'inspecting', 'node_code': 'inspect',
                       'node_name': '拆件检验',
                       'description': '设备拆解后、维修保养前状态记录'},
            'repair': {'status': 'repairing', 'node_code': 'repair',
                       'node_name': '维修保养',
                       'description': '进行设备维修保养操作'},
            'qc':     {'status': 'ready', 'node_code': 'qc',
                       'node_name': '质检通过',
                       'description': '设备质检通过，所有项目达标'},
            'ship':   {'status': 'shipped', 'node_code': 'shipped',
                       'node_name': '回寄客户',
                       'description': '已打包发出'},
            'complete':{'status': 'completed', 'node_code': 'completed',
                       'node_name': '订单完成',
                       'description': '客户已签收，订单完成'},
        }

        if step not in steps_map:
            return {'success': False, 'message': f'未知步骤: {step}'}, 400

        step_info = steps_map[step]
        params = [step_info['status'], now]
        update_sql = "UPDATE orders SET status = %s, updated_at = %s"

        if step in ('pay', 'create'):
            update_sql += ", payment_status = 'paid', payment_time = %s"
            params.append(now)
            item_data = request.get_json() or {}
            # 交付方式
            delivery_type = item_data.get('delivery_type', 'express')
            if delivery_type:
                cursor.execute('UPDATE orders SET delivery_type = %s WHERE id = %s', (delivery_type, order_id))
                if delivery_type == 'store':
                    step_info['description'] = '自行到店交付'
                else:
                    step_info['description'] = '快递寄送'
            if item_data.get('product_type_id'):
                pt_id = item_data.get('product_type_id')
                brand_id = item_data.get('brand_id') or None
                model_id = item_data.get('model_id') or None
                svc_id = item_data.get('service_type_id') or None
                price = 200.0
                if svc_id:
                    cursor.execute('SELECT base_price FROM service_types WHERE id = %s', (svc_id,))
                    r = cursor.fetchone()
                    if r and r['base_price']: price = float(r['base_price'])
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_type_id, brand_id, model_id,
                                          service_type_id, quantity, item_price, created_at)
                    VALUES (%s, %s, %s, %s, %s, 1, %s, NOW())
                """, (order_id, pt_id, brand_id, model_id, svc_id, price))
                cursor.execute('UPDATE orders SET total_amount = %s WHERE id = %s', (price, order_id))

        if step == 'receive':
            item_data = request.get_json() or {}
            express_company = item_data.get('express_company', '')
            express_no = item_data.get('express_no', '')
            packaging_condition = item_data.get('packaging_condition', '完好')  # 完好/破损
            if express_company or express_no:
                cursor.execute('UPDATE orders SET express_company = %s, express_no = %s WHERE id = %s',
                             (express_company, express_no, order_id))
                # 回填paid(确认收货)节点描述，加入快递信息
                desc_parts = ['确认收货']
                if express_company:
                    desc_parts.append(express_company)
                if express_no:
                    desc_parts.append(f"单号:{express_no}")
                cursor.execute("UPDATE tracking_nodes SET description = %s WHERE order_id = %s AND node_code = 'payment_update'",
                             (' '.join(desc_parts), order_id))

        if step == 'ship':
            item_data = request.get_json() or {}
            ret_company = item_data.get('return_express_company', '')
            ret_no = item_data.get('return_express_no', '')
            if ret_company or ret_no:
                cursor.execute('UPDATE orders SET return_express_company = %s, return_express_no = %s WHERE id = %s',
                             (ret_company, ret_no, order_id))

        if step == 'complete':
            update_sql += ", completed_at = %s"
            params.append(now)

        update_sql += " WHERE id = %s"
        params.append(order_id)
        cursor.execute(update_sql, params)

        # 使用前端传来的备注，否则用默认描述
        description = item_data.get('note', step_info['description']) or step_info['description']

        # 先插入节点（获取node_id），再保存照片
        cursor.execute("""
            INSERT INTO tracking_nodes (order_id, node_code, node_name, description,
                                      staff_id, staff_name, operate_time, photos, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, '[]', %s)
            RETURNING id
        """, (order_id, step_info['node_code'], step_info['node_name'],
              description, staff['id'], staff_name, now, now))
        new_node_id = cursor.fetchone()['id']

        # 保存照片到 nodes/{node_id}/ 目录（PDF从这个路径读取）
        node_photos = '[]'
        incoming_photos = item_data.get('photos', [])
        # receive步骤额外处理unbox照片
        unbox_photos = item_data.get('unbox_photos', [])
        if step == 'receive' and unbox_photos:
            incoming_photos = incoming_photos + unbox_photos  # 合并未拆邮包+拆邮包照片
        if incoming_photos and step not in ('pay', 'create', 'complete'):
            photos_list = []
            node_dir = os.path.join(photo_dir, 'nodes', str(new_node_id))
            os.makedirs(node_dir, exist_ok=True)
            import base64
            for i, photo_data in enumerate(incoming_photos[:5]):
                if photo_data and photo_data.startswith('data:'):
                    photo_b64 = photo_data.split(',')[1] if ',' in photo_data else photo_data
                    fname = f'{step}_{i+1}.jpg'
                    try:
                        img_data = base64.b64decode(photo_b64)
                        dest = os.path.join(node_dir, fname)
                        with open(dest, 'wb') as f:
                            f.write(img_data)
                        photos_list.append(fname)
                    except Exception:
                        pass
            if photos_list:
                node_photos = json.dumps(photos_list)
                cursor.execute("UPDATE tracking_nodes SET photos = %s WHERE id = %s",
                             (node_photos, new_node_id))

        conn.commit()

        # PDF在commit之后生成，确保新连接能看到所有已提交的节点
        # QC时生成初版，complete时生成最终版（包含全部8步）
        pdf_path = None
        if step in ('qc', 'complete'):
            import database as _db
            conn2 = _db.get_connection()
            cursor2 = conn2.cursor()
            try:
                cursor2.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
                updated_order = cursor2.fetchone()
                from pdf_generator import generate_order_pdf
                pdf_path = generate_order_pdf(updated_order, staff_name=staff_name)
                if pdf_path:
                    cursor2.execute('UPDATE orders SET pdf_path = %s WHERE id = %s', (pdf_path, order_id))
                    conn2.commit()
            finally:
                database.release_connection(conn2)

        return {'success': True,
                'data': {'step': step, 'status': step_info['status'], 'node_id': new_node_id, 'pdf_path': pdf_path}}, 200

    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': f'服务器内部错误: {e}'}, 500
    finally:
        database.release_connection(conn)


@console_bp.route('/simulate/cleanup', methods=['POST'])
def simulate_cleanup():
    """清理所有模拟订单"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff or staff['role'] != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可清理'}), 403

    conn = database.get_connection()
    cursor = conn.cursor()

    # 找模拟订单
    cursor.execute('SELECT id FROM orders WHERE is_simulation = 1')
    sim_orders = [r['id'] for r in cursor.fetchall()]

    if not sim_orders:
        database.release_connection(conn)
        return jsonify({'success': True, 'message': '无模拟订单需清理'})

    cleaned = 0
    for oid in sim_orders:
        # 删除status log
        cursor.execute('DELETE FROM order_status_log WHERE order_id = %s', (oid,))
        cursor.execute('DELETE FROM status_change_log WHERE order_id = %s', (oid,))
        # 删除tracking nodes
        cursor.execute('DELETE FROM tracking_nodes WHERE order_id = %s', (oid,))
        # 删除order items
        cursor.execute('DELETE FROM order_items WHERE order_id = %s', (oid,))
        # 删除special service records
        cursor.execute('DELETE FROM special_service_records WHERE order_id = %s', (oid,))
        # 删除订单
        cursor.execute('DELETE FROM orders WHERE id = %s', (oid,))
        # 删除照片目录
        photo_dir = f'{database.ORDER_UPLOAD_DIR}/{oid}'
        if os.path.exists(photo_dir):
            import shutil
            shutil.rmtree(photo_dir, ignore_errors=True)
        cleaned += 1

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': f'已清理{cleaned}个模拟订单'})



