# -*- coding: utf-8 -*-
"""客户端订单管理 (create, list, detail, edit, cancel, express, special-service, pdf, pay)"""
from . import client_bp
from auth import validate_customer_token
from .client_services import get_price, generate_order_no
import database
from psycopg2 import sql
from flask import request, jsonify, send_file
from datetime import datetime, timedelta
from pydantic import ValidationError
from validators import CreateOrder, EditOrder, ExpressUpdate, SpecialServiceRespond
from status_log import log_status_change
from notification import _integration_hook_notify
import json
import os

@client_bp.route('/orders', methods=['POST'])
def create_order():
    """创建订单"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    data = request.get_json()
    
    # Pydantic 校验
    try:
        validated = CreateOrder(**data)
    except ValidationError as e:
        return jsonify({'success': False, 'message': f'参数校验失败: {e.errors()[0]["msg"]}'}), 400
    
    items = [item.model_dump() for item in validated.items]

    if not items:
        return jsonify({'success': False, 'message': '订单项目不能为空'})  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()

    try:
        # 生成订单号
        order_no = generate_order_no()

        # 获取客户信息（检查是否是经销商）
        cursor.execute('SELECT is_dealer, discount_rate FROM customers WHERE id = %s', (customer['id'],))
        customer_info = cursor.fetchone()
        is_dealer = customer_info and customer_info['is_dealer'] == 1
        discount_rate = customer_info['discount_rate'] if customer_info else 100

        # 计算总金额
        total_amount = 0
        order_items_data = []

        for item in items:
            product_type_id = item.get('product_type_id')
            brand_id = item.get('brand_id')
            model_id = item.get('model_id')
            service_type_id = item.get('service_type_id')
            quantity = item.get('quantity', 1)

            # 获取实际价格
            price = get_price(conn, product_type_id, brand_id, model_id, service_type_id)
            
            # 经销商折扣（仅基础服务价格参与折扣，加急和专项服务不参与）
            if is_dealer and discount_rate and discount_rate != 100:
                final_price = round(price * discount_rate / 100, 2)  # pragma: no cover
            else:
                final_price = price
            
            item_total = final_price * quantity
            total_amount += item_total

            category = item.get('category', '')
            order_items_data.append({
                'product_type_id': product_type_id,
                'brand_id': brand_id,
                'model_id': model_id,
                'quantity': quantity,
                'service_type_id': service_type_id,
                'category': category,
                'item_price': price,
                'final_price': final_price,
                'discount_rate': discount_rate if is_dealer else 100
            })
        
        # 加急服务费用（不参与经销商折扣）
        urgent_service = data.get('urgent_service', 0)
        urgent_fee = 100.0 if urgent_service else 0.0
        total_amount += urgent_fee

        # 创建订单
        cursor.execute('''
            INSERT INTO orders (
                order_no, customer_id, receiver_name, receiver_phone, receiver_address,
                total_amount, freight_amount, customer_remark, express_company, express_no,
                status, payment_status, source, delivery_type, urgent_service, urgent_fee,
                created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'confirmed', 'unpaid', 'wechat', %s, %s, %s,
                      NOW(), NOW())
            RETURNING id
        ''', (
            order_no,
            customer['id'],
            data.get('receiver_name', ''),
            data.get('receiver_phone', ''),
            data.get('receiver_address', ''),
            total_amount,
            data.get('freight_amount', 0),
            data.get('customer_remark', ''),
            data.get('express_company', ''),
            data.get('express_no', ''),
            data.get('delivery_type', 'store'),
            urgent_service,
            urgent_fee
        ))

        order_id = cursor.fetchone()['id']

        # 创建订单明细
        for item_data in order_items_data:
            cursor.execute('''
                INSERT INTO order_items (
                    order_id, product_type_id, brand_id, model_id,
                    quantity, service_type_id, item_price, category,
                    discount_rate, final_price
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                order_id,
                item_data['product_type_id'],
                item_data['brand_id'],
                item_data['model_id'],
                item_data['quantity'],
                item_data['service_type_id'],
                item_data['item_price'],
                item_data.get('category', ''),
                item_data['discount_rate'],
                item_data['final_price']
            ))

        # 创建初始追踪节点
        cursor.execute('''
            INSERT INTO tracking_nodes (
                order_id, node_code, node_name, description, operate_time
            ) VALUES (%s, 'created', '订单确认', '客户确认订单', NOW())
        ''', (order_id,))

        conn.commit()

        return jsonify({
            'success': True,
            'data': {
                'id': order_id,
                'order_no': order_no,
                'total_amount': total_amount,
                'status': 'confirmed'
            }
        })

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'创建订单失败: {str(e)}'})
    finally:
        database.release_connection(conn)

@client_bp.route('/orders/my', methods=['GET'])
def get_my_orders():
    """获取我的订单列表（优化：2次查询替代N+1）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, order_no, total_amount, status, payment_status,
               created_at, express_company, express_no
        FROM orders
        WHERE customer_id = %s AND status != 'deleted'
        ORDER BY created_at DESC
    ''', (customer['id'],))
    orders_data = cursor.fetchall()

    orders = []
    if orders_data:
        # 一次查询批量获取所有订单项（消除N+1）
        order_ids = [o['id'] for o in orders_data]
        cursor.execute('''
            SELECT oi.*, pt.name as product_type_name, b.name as brand_name,
                   m.name as model_name, st.name as service_type_name
            FROM order_items oi
            LEFT JOIN product_types pt ON oi.product_type_id = pt.id
            LEFT JOIN brands b ON oi.brand_id = b.id
            LEFT JOIN models m ON oi.model_id = m.id
            LEFT JOIN service_types st ON oi.service_type_id = st.id
            WHERE oi.order_id = ANY(%s)
        ''', (order_ids,))
        all_items = cursor.fetchall()

        # 按 order_id 分组
        items_by_order = {}
        for item in all_items:
            oid = item['order_id']
            if oid not in items_by_order:
                items_by_order[oid] = []
            items_by_order[oid].append(item)

        for order in orders_data:
            items = items_by_order.get(order['id'], [])
            order['items'] = items

            # 提取第一个订单项的主要信息(用于列表展示),优先用自定义文字
            if items:
                first_item = items[0]
                order['productName'] = first_item.get('product_type_name', '') or ''
                order['brandName'] = first_item.get('brand_name_text') or first_item.get('brand_name', '') or ''
                order['model'] = first_item.get('model_name_text') or first_item.get('model_name', '') or ''
                order['serviceName'] = first_item.get('service_name_text') or first_item.get('service_type_name', '') or ''
                order['servicePrice'] = first_item.get('item_price', 0) or 0
            else:
                order['productName'] = ''
                order['brandName'] = ''
                order['model'] = ''
                order['serviceName'] = ''
                order['servicePrice'] = 0

            orders.append(order)

    database.release_connection(conn)
    return jsonify({'success': True, 'data': orders})

@client_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order_detail(order_id):
    """获取订单详情"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 获取订单信息
    cursor.execute('''
        SELECT * FROM orders WHERE id = %s AND customer_id = %s
    ''', (order_id, customer['id']))
    order = cursor.fetchone()

    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})
    if str(order['customer_id']) != str(customer['id']):
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': '无权访问此订单'}), 403  # pragma: no cover

    order_dict = order
    # 确保 delivery_type 字段存在
    if 'delivery_type' not in order_dict:
        order_dict['delivery_type'] = 'store'  # pragma: no cover

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
    items = []
    for r in cursor.fetchall():
        item = r
        # 自定义文字覆盖JOIN结果
        if item.get('brand_name_text'):
            item['brand_name'] = item['brand_name_text']
        if item.get('model_name_text'):
            item['model_name'] = item['model_name_text']
        if item.get('service_name_text'):
            item['service_type_name'] = item['service_name_text']
        items.append(item)
    order_dict['items'] = items

    # 获取追踪节点
    cursor.execute('''
        SELECT * FROM tracking_nodes WHERE order_id = %s ORDER BY created_at
    ''', (order_id,))
    nodes = [r for r in cursor.fetchall()]

    # 解析photos字段并转换为完整URL
    for node in nodes:
        if node.get('photos'):
            try:
                filenames = json.loads(node['photos'])
                # 处理两种格式：字符串数组 或 对象数组 [{"type": "...", "path": "..."}]
                urls = []
                for f in filenames:
                    if isinstance(f, dict):
                        # 对象格式，提取path字段
                        path = f.get('path', '')
                        if path:
                            urls.append(f'/uploads/{path}' if not path.startswith('/') else path)
                    elif isinstance(f, str):
                        # 字符串格式
                        urls.append(
                            f'/uploads/orders/{order_id}/nodes/{node["id"]}/{f}' if not f.startswith('orders/') else f'/uploads/{f}'
                        )
                node['photos'] = urls
            except (KeyError, ValueError, TypeError):  # pragma: no cover
                node['photos'] = []

    order_dict['tracking_nodes'] = nodes

    # 获取专项服务记录
    cursor.execute('''
        SELECT ssr.*, ss.name as preset_name
        FROM special_service_records ssr
        LEFT JOIN special_services ss ON ssr.special_service_id = ss.id
        WHERE ssr.order_id = %s
    ''', (order_id,))
    order_dict['special_services'] = [r for r in cursor.fetchall()]

    database.release_connection(conn)
    return jsonify({'success': True, 'data': order_dict})

@client_bp.route('/orders/<int:order_id>/edit', methods=['PUT'])
def edit_order(order_id):
    """客户修改订单信息(仅进行中订单允许)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属
    cursor.execute('''
        SELECT id, status FROM orders WHERE id = %s AND customer_id = %s
    ''', (order_id, customer['id']))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    # 只有进行中的订单允许修改(维修员开始操作后禁止)
    allowed_statuses = ['unpaid', 'paid', 'confirmed', 'receiving']
    if order['status'] not in allowed_statuses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '当前状态不允许修改订单信息'})

    data = request.get_json()

    # 更新收件信息
    receiver_name = data.get('receiver_name')
    receiver_phone = data.get('receiver_phone')
    receiver_address = data.get('receiver_address')

    if receiver_name or receiver_phone or receiver_address:
        cursor.execute('''
            UPDATE orders SET receiver_name = COALESCE(%s, receiver_name),
                receiver_phone = COALESCE(%s, receiver_phone),
                receiver_address = COALESCE(%s, receiver_address),
                updated_at = NOW()
            WHERE id = %s
        ''', (receiver_name, receiver_phone, receiver_address, order_id))

    # 更新订单项
    items = data.get('items')
    if items and isinstance(items, list):
        for item in items:
            item_id = item.get('id')
            if not item_id:
                continue
            updates = []
            params = []
            if item.get('product_type_id') is not None:
                updates.append('product_type_id = %s')
                params.append(item['product_type_id'])
            if item.get('brand_id') is not None:
                updates.append('brand_id = %s')
                params.append(item['brand_id'])
                # 品牌:如果是自定义文字(ID不存在),存到 brand_name_text
                if item.get('brand_name'):
                    updates.append('brand_name_text = %s')
                    params.append(item['brand_name'])
            if item.get('model_id') is not None:
                updates.append('model_id = %s')
                params.append(item['model_id'])
                if item.get('model_name'):
                    updates.append('model_name_text = %s')
                    params.append(item['model_name'])
            if item.get('service_type_id') is not None:
                updates.append('service_type_id = %s')
                params.append(item['service_type_id'])
                if item.get('service_name'):
                    updates.append('service_name_text = %s')
                    params.append(item['service_name'])
            if item.get('category'):
                updates.append('category = %s')
                params.append(item['category'])
            if item.get('customer_note') is not None:
                updates.append('customer_note = %s')
                params.append(item['customer_note'])
            if updates:
                params.append(item_id)
                sql = 'UPDATE order_items SET ' + ', '.join(updates) + ' WHERE id = %s AND order_id = %s'
                cursor.execute(sql, params + [order_id])

    # 重新计算订单总额（因 items 变更可能导致价格变化）
    if items:
        cursor.execute('''
            SELECT id, product_type_id, brand_id, model_id, service_type_id, quantity
            FROM order_items WHERE order_id = %s
        ''', (order_id,))
        new_total = 0
        for ri in cursor.fetchall():
            price = get_price(conn, ri['product_type_id'], ri['brand_id'], ri['model_id'], ri['service_type_id'])
            item_total = price * (ri['quantity'] or 1)
            new_total += item_total
            cursor.execute('UPDATE order_items SET item_price = %s, final_price = %s WHERE id = %s',
                          (price, price, ri['id']))
        # 加上加急费、运费
        cursor.execute('SELECT COALESCE(urgent_fee, 0) as uf, COALESCE(freight_amount, 0) as fa FROM orders WHERE id = %s', (order_id,))
        extras = cursor.fetchone()
        new_total += float(extras['uf'] or 0)
        cursor.execute('UPDATE orders SET total_amount = %s WHERE id = %s', (new_total, order_id))

    # 更新备注
    note = data.get('customer_note')
    if note is not None:
        cursor.execute('''
            UPDATE orders SET customer_remark = %s, updated_at = NOW()
            WHERE id = %s
        ''', (note, order_id))

    conn.commit()
    database.release_connection(conn)
    return jsonify({'success': True, 'message': '订单信息已更新'})

@client_bp.route('/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    """客户取消订单（仅confirmed/received状态可取消）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, status FROM orders WHERE id = %s AND customer_id = %s
    ''', (order_id, customer['id']))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    cancellable = ['confirmed', 'received']
    if order['status'] not in cancellable:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '当前状态不允许取消，请联系客服'})

    old_status = order['status']
    cursor.execute('''
        UPDATE orders SET status = 'cancelled', updated_at = NOW()
        WHERE id = %s
    ''', (order_id,))
    log_status_change(conn, order_id, 'status', old_status, 'cancelled', customer['nickname'] or customer['phone'], 'client')
    conn.commit()
    _integration_hook_notify(conn, order_id, 'client', 'cancelled')
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '订单已取消'})

@client_bp.route('/orders/<int:order_id>/express', methods=['PUT'])
def update_express(order_id):
    """填写快递信息"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    data = request.get_json()
    express_company = data.get('express_company', '')
    express_no = data.get('express_no', '')

    if not express_company or not express_no:
        return jsonify({'success': False, 'message': '快递公司和快递单号不能为空'})  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属
    cursor.execute('''
        SELECT id FROM orders WHERE id = %s AND customer_id = %s
    ''', (order_id, customer['id']))
    if not cursor.fetchone():
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    cursor.execute('''
        UPDATE orders
        SET express_company = %s, express_no = %s, updated_at = NOW()
        WHERE id = %s
    ''', (express_company, express_no, order_id))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '快递信息更新成功'})

# ========== 专项服务响应 ==========

@client_bp.route('/orders/<int:order_id>/special-service/respond', methods=['POST'])
def respond_special_service(order_id):
    """响应专项服务"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    data = request.get_json()
    record_id = data.get('record_id')
    action = data.get('action')  # confirm 或 reject
    paid = data.get('paid', False)

    if not record_id or action not in ['confirm', 'reject']:
        return jsonify({'success': False, 'message': '参数错误'})

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属
    cursor.execute('''
        SELECT id FROM orders WHERE id = %s AND customer_id = %s
    ''', (order_id, customer['id']))
    if not cursor.fetchone():
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    # 更新专项服务记录
    if action == 'confirm':
        cursor.execute('''
            UPDATE special_service_records
            SET status = %s, confirmed_at = NOW()
            WHERE id = %s AND order_id = %s
        ''', ('confirmed' if not paid else 'paid', record_id, order_id))
    else:
        cursor.execute('''
            UPDATE special_service_records
            SET status = 'rejected'
            WHERE id = %s AND order_id = %s
        ''', (record_id, order_id))

    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '操作成功'})

@client_bp.route('/orders/<int:order_id>/special-services', methods=['GET'])
def get_order_special_services(order_id):
    """查看订单的专项服务列表（客户端）"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属
    cursor.execute('''
        SELECT id FROM orders WHERE id = %s AND customer_id = %s
    ''', (order_id, customer['id']))
    if not cursor.fetchone():
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'})

    cursor.execute('''
        SELECT sr.id, sr.special_service_id, sr.name, sr.price, sr.quantity,
               sr.status, sr.confirmed_at, sr.created_at,
               ss.name as service_name, ss.description
        FROM special_service_records sr
        LEFT JOIN special_services ss ON sr.special_service_id = ss.id
        WHERE sr.order_id = %s
        ORDER BY sr.created_at ASC
    ''', (order_id,))
    records = cursor.fetchall()
    database.release_connection(conn)

    return jsonify({'success': True, 'data': [dict(r) for r in records]})

# ========== PDF下载 ==========

@client_bp.route('/orders/<int:order_id>/pdf', methods=['GET'])
def download_pdf(order_id):
    """下载订单PDF(始终重新生成,确保包含完整7步节点)"""
    import time as _time
    # 支持Header和query参数两种token传递(<a>标签无法设Header)
    token = request.headers.get('Authorization', '').replace('Bearer ', '') or request.args.get('token', '')
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': '未登录或token已过期'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = %s AND customer_id = %s', (order_id, customer['id']))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': '订单不存在'})  # pragma: no cover

    order_dict = order

    # 始终重新生成PDF(包含所有追踪节点,含shipped/completed)
    import pdf_generator
    pdf_path = pdf_generator.generate_order_pdf(order_dict, conn, staff_name='')

    # 更新订单的pdf_path
    cursor.execute('UPDATE orders SET pdf_path = %s WHERE id = %s', (pdf_path, order_id))
    conn.commit()
    database.release_connection(conn)

    # 客户端:PDF超过15天不可下载(管理员不受限制)
    if pdf_path and os.path.exists(pdf_path):
        pdf_age_days = (_time.time() - os.path.getmtime(pdf_path)) / 86400
        pdf_expiry_days = int(os.getenv('PDF_EXPIRY_DAYS', '15'))
        if pdf_age_days > pdf_expiry_days:
            return jsonify({'success': False, 'message': '维修报告已过期(超过15天),如需查阅请联系皓壹潜水中心'})
        return send_file(pdf_path, as_attachment=True, download_name=f"{order['order_no']}.pdf")
    else:
        return jsonify({'success': False, 'message': 'PDF文件不存在'})


# ========== 模拟支付 ==========
@client_bp.route('/orders/<int:order_id>/pay', methods=['POST'])
def mock_pay(order_id):
    """确认订单(需认证+订单归属)"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '').replace('X-Customer-Token:', '').strip()
    if not token:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    customer = validate_customer_token(token)
    if not customer:
        return jsonify({'success': False, 'message': 'token无效'}), 401  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证订单归属并获取当前状态
    cursor.execute('SELECT id, status, payment_status FROM orders WHERE id = %s AND customer_id = %s', (order_id, customer['id']))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无权操作此订单'}), 403

    old_status = order['status']
    old_payment_status = order['payment_status']

    # 只允许 unpaid/pending 状态的订单确认（防止已发货订单被意外回退）
    cursor.execute('''
        UPDATE orders
        SET payment_status = 'paid', status = 'confirmed',
            payment_time = NOW(),
            updated_at = NOW()
        WHERE id = %s AND customer_id = %s AND status IN ('unpaid', 'pending')
    ''', (order_id, customer['id']))
    if cursor.rowcount == 0:
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': '订单状态不允许确认'})  # pragma: no cover

    log_status_change(conn, order_id, 'status', old_status, 'confirmed', customer['nickname'] or customer['phone'], 'client')
    log_status_change(conn, order_id, 'payment_status', old_payment_status, 'paid', customer['nickname'] or customer['phone'], 'client')
    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '订单确认成功'})


# ========== 追踪节点 ==========
