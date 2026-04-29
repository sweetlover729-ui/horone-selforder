# -*- coding: utf-8 -*-
"""
统一认证模块
"""
import database
import secrets
from functools import wraps
from flask import jsonify, request

def generate_token():
    """生成32位随机token"""
    return secrets.token_hex(16)

def validate_staff_token(token, allow_inactive=False):
    """验证员工token
    allow_inactive=True 时跳过 is_active 检查（用于禁用自己等操作）
    """
    if not token:
        return None
    conn = database.get_connection()
    cursor = conn.cursor()
    if allow_inactive:
        cursor.execute('''
            SELECT s.id as staff_id, s.username, s.password_hash, s.full_name,
                   s.role, s.is_active, s.created_at,
                   st.id as token_id, st.token, st.expires_at
            FROM staff_tokens st
            JOIN staff s ON st.staff_id = s.id
            WHERE st.token = %s AND st.expires_at > NOW()
        ''', (token,))
    else:
        cursor.execute('''
            SELECT s.id as staff_id, s.username, s.password_hash, s.full_name,
                   s.role, s.is_active, s.created_at,
                   st.id as token_id, st.token, st.expires_at
            FROM staff_tokens st
            JOIN staff s ON st.staff_id = s.id
            WHERE st.token = %s AND st.expires_at > NOW()
            AND s.is_active = 1
        ''', (token,))
    result = cursor.fetchone()
    database.release_connection(conn)
    if result:
        d = result
        d['id'] = d['staff_id']
        return d
    return None

def validate_customer_token(token):
    """验证客户token"""
    if not token:
        return None
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ct.id as token_id, ct.token, ct.expires_at,
               c.id, c.name, c.nickname, c.phone, c.openid, c.created_at
        FROM customer_tokens ct
        JOIN customers c ON ct.customer_id = c.id
        WHERE ct.token = %s AND ct.expires_at > NOW()
    ''', (token,))
    result = cursor.fetchone()
    database.release_connection(conn)
    return result if result else None

def require_admin(token):
    """检查token是否属于admin/super_admin角色"""
    if not token:
        return False
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM staff_tokens st
        JOIN staff s ON st.staff_id = s.id
        WHERE st.token = %s AND st.expires_at > NOW()
          AND s.is_active = 1
          AND s.role IN ('admin', 'super_admin')
    ''', (token,))
    result = cursor.fetchone()
    database.release_connection(conn)
    return result is not None

def admin_required(f):
    """装饰器：要求admin/super_admin角色"""
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Staff-Token', '')
        if not require_admin(token):
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    decorated.__doc__ = f.__doc__
    decorated.__module__ = f.__module__
    return decorated
