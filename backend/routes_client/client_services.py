# -*- coding: utf-8 -*-
"""客户端服务与价格 (services, special-services, get_price, generate_order_no, price routes)"""
from . import client_bp
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime
from decimal import Decimal

@client_bp.route('/services', methods=['GET'])
def get_services():
    """获取服务类型列表+价格(支持按套装类型过滤)"""
    type_id = request.args.get('type_id', type=int)
    category = request.args.get('category', '').strip()
    conn = database.get_connection()
    cursor = conn.cursor()

    if type_id:
        if category:
            # 过滤包含指定套装类型的服务
            cursor.execute('''
                SELECT id, product_type_id, name, description, base_price, sort_order
                FROM service_types
                WHERE product_type_id = %s AND is_active = 1 AND name LIKE %s
                ORDER BY sort_order
            ''', (type_id, f'%{category}%'))
        else:
            cursor.execute('''
                SELECT id, product_type_id, name, description, base_price, sort_order
                FROM service_types
                WHERE product_type_id = %s AND is_active = 1
                ORDER BY sort_order
            ''', (type_id,))
    else:
        cursor.execute('''
            SELECT id, product_type_id, name, description, base_price, sort_order
            FROM service_types
            WHERE is_active = 1
            ORDER BY sort_order
        ''')

    services = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': services})

@client_bp.route('/special-services', methods=['GET'])
def get_special_services():
    """获取专项服务预设列表"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, description, preset_price
        FROM special_services
        WHERE is_active = 1 ORDER BY name
    ''')
    services = [row for row in cursor.fetchall()]
    database.release_connection(conn)
    return jsonify({'success': True, 'data': services})

# ========== 订单(需client token) ==========

def get_price(conn, product_type_id, brand_id, model_id, service_type_id):
    """获取实际价格 = 服务类型基础价 + 价格配置加价
    price_overrides.price 是叠加在 base_price 上的加价，不是最终价格"""
    cursor = conn.cursor()

    # 获取服务类型基础价
    cursor.execute('SELECT base_price FROM service_types WHERE id = %s', (service_type_id,))
    base_result = cursor.fetchone()
    base_price = base_result['base_price'] if base_result else 0

    # 查找加价配置（优先精确匹配）
    surcharge = 0

    # 先查找精确匹配（含型号）
    cursor.execute('''
        SELECT price FROM price_overrides
        WHERE product_type_id = %s AND brand_id = %s AND model_id = %s AND service_type_id = %s
    ''', (product_type_id, brand_id, model_id, service_type_id))
    result = cursor.fetchone()
    if result:
        surcharge = result['price']  # pragma: no cover
        return base_price + surcharge  # pragma: no cover

    # 查找品牌级别的加价
    cursor.execute('''
        SELECT price FROM price_overrides
        WHERE product_type_id = %s AND brand_id = %s AND model_id IS NULL AND service_type_id = %s
    ''', (product_type_id, brand_id, service_type_id))
    result = cursor.fetchone()
    if result:
        surcharge = result['price']  # pragma: no cover
        return base_price + surcharge  # pragma: no cover

    # 无加价配置，返回基础价
    return base_price

def generate_order_no():
    """生成订单号 RMD-YYYYMMDD-XXXXXX,基于MAX保证无间隙且唯一"""
    today = datetime.now().strftime('%Y%m%d')
    conn = database.get_connection()
    cursor = conn.cursor()

    # 找今日最大序号
    cursor.execute('''
        SELECT order_no FROM orders
        WHERE order_no LIKE %s
        ORDER BY order_no DESC LIMIT 1
    ''', (f'RMD-{today}%',))
    row = cursor.fetchone()
    if row:
        # 从最大号+1
        last = row['order_no']  # e.g. RMD-20260422-000005
        seq = int(last.split('-')[-1]) + 1
    else:
        seq = 1  # pragma: no cover

    database.release_connection(conn)
    return f"RMD-{today}-{seq:06d}"

@client_bp.route('/price', methods=['GET'])
def get_order_price():
    """查询价格：基础价 + 品牌加价 = 最终价"""
    product_type_id = request.args.get('product_type_id', type=int)
    brand_id = request.args.get('brand_id', type=int)
    model_id = request.args.get('model_id', type=int)
    service_type_id = request.args.get('service_type_id', type=int)

    if not product_type_id or not brand_id or not service_type_id:
        return jsonify({'success': False, 'message': '缺少必要参数'})

    conn = database.get_connection()
    try:
        # 获取基础价
        cursor = conn.cursor()
        cursor.execute('SELECT base_price, name FROM service_types WHERE id = %s', (service_type_id,))
        svc = cursor.fetchone()
        if not svc:
            return jsonify({'success': False, 'message': '服务类型不存在'})
        base_price = svc['base_price']

        # 查找加价
        surcharge = 0
        # 精确匹配（含型号）
        if model_id:
            cursor.execute('''
                SELECT price FROM price_overrides
                WHERE product_type_id = %s AND brand_id = %s AND model_id = %s AND service_type_id = %s
            ''', (product_type_id, brand_id, model_id, service_type_id))
            result = cursor.fetchone()
            if result:
                surcharge = result['price']  # pragma: no cover
        # 品牌级别匹配
        if not surcharge:
            cursor.execute('''
                SELECT price FROM price_overrides
                WHERE product_type_id = %s AND brand_id = %s AND model_id IS NULL AND service_type_id = %s
            ''', (product_type_id, brand_id, service_type_id))
            result = cursor.fetchone()
            if result:
                surcharge = result['price']  # pragma: no cover

        return jsonify({
            'success': True,
            'data': {
                'base_price': base_price,
                'surcharge': surcharge,
                'final_price': base_price + surcharge
            }
        })
    finally:
        database.release_connection(conn)


@client_bp.route('/prices', methods=['GET'])
def get_all_prices():
    """批量查询品牌所有服务的加价配置，返回 {service_type_id: surcharge} """
    product_type_id = request.args.get('product_type_id', type=int)
    brand_id = request.args.get('brand_id', type=int)
    model_id = request.args.get('model_id', type=int)

    if not product_type_id or not brand_id:
        return jsonify({'success': False, 'message': '缺少必要参数'})

    conn = database.get_connection()
    try:
        cursor = conn.cursor()

        # 品牌级别加价（model_id IS NULL）
        cursor.execute('''
            SELECT service_type_id, price FROM price_overrides
            WHERE product_type_id = %s AND brand_id = %s AND model_id IS NULL
        ''', (product_type_id, brand_id))
        surcharges = {row['service_type_id']: row['price'] for row in cursor.fetchall()}

        # 型号级别加价覆盖品牌级别
        if model_id:
            cursor.execute('''
                SELECT service_type_id, price FROM price_overrides
                WHERE product_type_id = %s AND brand_id = %s AND model_id = %s
            ''', (product_type_id, brand_id, model_id))
            for row in cursor.fetchall():
                surcharges[row['service_type_id']] = row['price']  # pragma: no cover

        return jsonify({
            'success': True,
            'data': surcharges
        })
    finally:
        database.release_connection(conn)

