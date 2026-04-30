# -*- coding: utf-8 -*-
"""Console API — Staff authentication"""

from flask import request, jsonify
import database
import json
import os
from datetime import datetime, timedelta
from psycopg2 import sql
from logging_config import get_logger
from auth import validate_staff_token, generate_token
import secrets
import bcrypt
from pydantic import ValidationError
from validators import StaffLogin

from . import console_bp

logger = get_logger('routes_console.auth')


@console_bp.route('/auth/login', methods=['POST'])
def staff_login():
    """员工登录"""
    data = request.get_json()
    
    # Pydantic 校验
    try:
        validated = StaffLogin(**data)
    except ValidationError as e:
        return jsonify({'success': False, 'message': f'参数校验失败: {e.errors()[0]["msg"]}'}), 400
    
    username = validated.username
    password = validated.password

    conn = database.get_connection()
    cursor = conn.cursor()

    # 查找用户
    cursor.execute('''
        SELECT * FROM staff WHERE username = %s AND is_active = 1
    ''', (username,))
    staff = cursor.fetchone()

    if not staff:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '用户名或密码错误'})

    # 验证密码（支持 bcrypt + SHA256 双验证）
    is_valid, needs_rehash = database.verify_password(password, staff['password_hash'])
    if not is_valid:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '用户名或密码错误'})

    # SHA256 密码升级为 bcrypt
    if needs_rehash:
        new_hash = database.hash_password(password)
        cursor.execute('UPDATE staff SET password_hash = %s WHERE id = %s', (new_hash, staff['id']))

    # 清理该staff所有过期token + 活跃旧token（防止token膨胀）
    cursor.execute('DELETE FROM staff_tokens WHERE expires_at::timestamp < NOW()')
    cursor.execute('DELETE FROM staff_tokens WHERE staff_id = %s AND expires_at::timestamp > NOW()', (staff['id'],))

    # 生成新token
    token = generate_token()
    expires_at = datetime.now() + timedelta(hours=24)

    cursor.execute('''
        INSERT INTO staff_tokens (staff_id, token, expires_at)
        VALUES (%s, %s, %s)
    ''', (staff['id'], token, expires_at))
    conn.commit()
    database.release_connection(conn)

    return jsonify({
        'success': True,
        'staff': {
            'id': staff['id'],
            'username': staff['username'],
            'full_name': staff['full_name'],
            'role': staff['role']
        },
        'token': token
    })

@console_bp.route('/auth/me', methods=['GET'])
def get_me():
    """获取当前员工信息"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    return jsonify({
        'success': True,
        'staff': {
            'id': staff['id'],
            'username': staff['username'],
            'full_name': staff['full_name'],
            'role': staff['role']
        }
    })

@console_bp.route('/auth/password', methods=['PUT'])
def change_password():
    """修改密码"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'success': False, 'message': '原密码和新密码不能为空'})

    # 验证原密码（支持 bcrypt + SHA256 双验证）
    is_valid, needs_rehash = database.verify_password(old_password, staff['password_hash'])
    if not is_valid:
        return jsonify({'success': False, 'message': '原密码错误'})

    conn = database.get_connection()
    cursor = conn.cursor()
    new_hash = database.hash_password(new_password)
    cursor.execute('''
        UPDATE staff SET password_hash = %s WHERE id = %s
    ''', (new_hash, staff['id']))
    conn.commit()
    database.release_connection(conn)

    return jsonify({'success': True, 'message': '密码修改成功'})


