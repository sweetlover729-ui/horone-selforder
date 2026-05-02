# -*- coding: utf-8 -*-
"""客户端认证 (wechat-login, phone-login)"""
from . import client_bp
from auth import validate_customer_token, generate_token
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime, timedelta
from pydantic import ValidationError
from validators import CustomerPhoneLogin
import secrets
from notification import _integration_hook_notify

@client_bp.route('/auth/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录(开发阶段支持模拟登录)"""
    data = request.get_json()
    code = data.get('code', '')

    conn = database.get_connection()
    cursor = conn.cursor()

    if code == 'mock_login':
        # 模拟登录
        openid = data.get('openid', 'mock_openid_' + secrets.token_hex(8))
        nickname = data.get('nickname', '测试用户')

        # 查找或创建客户
        cursor.execute("SELECT * FROM customers WHERE openid = %s", (openid,))
        customer = cursor.fetchone()

        if not customer:
            cursor.execute('''
                INSERT INTO customers (openid, nickname, updated_at)
                VALUES (%s, %s, NOW())
            ''', (openid, nickname))
            conn.commit()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM customers WHERE openid = %s", (openid,))
            customer = cursor.fetchone()
    else:
        # 实际微信登录(待实现)
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '微信登录暂未实现,请使用模拟登录'})

    # 清理该customer过期token（防止膨胀）
    cursor.execute('DELETE FROM customer_tokens WHERE expires_at::timestamp < NOW()')
    cursor.execute('DELETE FROM customer_tokens WHERE customer_id = %s AND expires_at::timestamp > NOW()', (customer['id'],))

    # 生成token
    token = generate_token()
    expires_at = (datetime.now() + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO customer_tokens (customer_id, token, expires_at)
        VALUES (%s, %s, %s)
    ''', (customer['id'], token, expires_at))
    conn.commit()
    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {
            'id': customer['id'],
            'openid': customer['openid'],
            'nickname': customer['nickname'],
            'name': customer['name'],
            'phone': customer['phone'],
            'address': customer['address'],
            'token': token
        }
    })

@client_bp.route('/auth/phone-login', methods=['POST'])
def phone_login():
    """手机号+姓名登录(或注册)"""
    data = request.get_json()
    phone = (data.get('phone', '') or '').strip()
    name = (data.get('name', '') or '').strip()

    # Pydantic 校验
    try:
        validated = CustomerPhoneLogin(phone=phone, name=name)
    except ValidationError as e:
        return jsonify({'success': False, 'message': f'参数校验失败: {e.errors()[0]["msg"]}'}), 400

    if not phone or not name:
        return jsonify({'success': False, 'message': '请填写姓名和手机号'})

    # 手机号格式简单校验(11位数字)
    if len(phone) != 11 or not phone.isdigit():
        return jsonify({'success': False, 'message': '手机号格式不正确'})

    conn = database.get_connection()
    cursor = conn.cursor()

    # 查找已有客户(按手机号优先,其次姓名)
    cursor.execute(
        "SELECT * FROM customers WHERE phone = %s", (phone,)
    )
    customer = cursor.fetchone()

    if customer:
        # 已存在:更新姓名(如果姓名空或不同)
        if not customer['name'] or customer['name'] != name:
            cursor.execute(
                "UPDATE customers SET name = %s, updated_at = NOW() WHERE id = %s RETURNING *",
                (name, customer['id'])
            )
            conn.commit()
            customer = cursor.fetchone()
    else:
        # 新建客户(无 openid,用 NULL 避免 UNIQUE 冲突)
        cursor.execute('''
            INSERT INTO customers (openid, name, phone, nickname, updated_at)
            VALUES (NULL, %s, %s, %s, NOW())
            RETURNING *
        ''', (name, phone, name))
        customer = cursor.fetchone()
        conn.commit()

    # 清理该customer过期token + 活跃旧token（防止膨胀）
    cursor.execute('DELETE FROM customer_tokens WHERE expires_at::timestamp < NOW()')
    cursor.execute('DELETE FROM customer_tokens WHERE customer_id = %s AND expires_at::timestamp > NOW()', (customer['id'],))

    # 生成 token
    token = generate_token()
    expires_at = (datetime.now() + timedelta(hours=24 * 30)).strftime('%Y-%m-%d %H:%M:%S')  # 手机号登录有效期30天

    cursor.execute('''
        INSERT INTO customer_tokens (customer_id, token, expires_at)
        VALUES (%s, %s, %s)
    ''', (customer['id'], token, expires_at))
    conn.commit()
    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {
            'id': customer['id'],
            'openid': customer['openid'] or None,
            'nickname': customer['nickname'] or name,
            'name': customer['name'],
            'phone': customer['phone'],
            'address': customer['address'],
            'token': token
        }
    })

# ========== 产品数据(无需登录) ==========
