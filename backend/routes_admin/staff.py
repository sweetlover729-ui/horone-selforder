# -*- coding: utf-8 -*-
"""员工管理 (staff CRUD)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
from psycopg2 import sql
from flask import request, jsonify
from datetime import datetime

@admin_required
@admin_bp.route('/staff', methods=['GET'])
def get_staff():
    """获取员工列表"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, full_name, role, is_active, created_at FROM staff ORDER BY id')
    data = []
    for row in cursor.fetchall():
        data.append({
            'id': row['id'],
            'username': row['username'],
            'fullName': row['full_name'],
            'full_name': row['full_name'],
            'role': row['role'],
            'is_active': row['is_active'],
            'createdAt': row['created_at'].isoformat() if row['created_at'] else None,
            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
        })
    database.release_connection(conn)
    return jsonify({'success': True, 'data': data})

@admin_required
@admin_bp.route('/staff', methods=['POST'])
def create_staff():
    """创建员工账号"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    full_name = data.get('full_name', '') or data.get('fullName', '')
    role = data.get('role', 'technician')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # 检查用户名是否已存在
    cursor.execute('SELECT id FROM staff WHERE username = %s', (username,))
    if cursor.fetchone():
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '用户名已存在'})
    
    password_hash = database.hash_password(password)
    cursor.execute('''
        INSERT INTO staff (username, password_hash, full_name, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (username, password_hash, full_name, role))
    new_id = cursor.fetchone()['id']
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True, 'id': new_id})

@admin_required
@admin_bp.route('/staff/<int:staff_id>', methods=['PUT'])
def update_staff(staff_id):
    """更新员工账号"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    data = request.get_json()
    conn = database.get_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    params = []
    
    # 兼容前端驼峰 fullName 和蛇形 full_name
    if 'fullName' in data and 'full_name' not in data:
        data['full_name'] = data['fullName']
    for field in ['username', 'full_name', 'role', 'is_active']:
        if field in data:
            set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier(field)))
            params.append(data[field])
    
    if 'password' in data and data['password']:
        set_clauses.append(sql.SQL('{} = %s').format(sql.Identifier('password_hash')))
        params.append(database.hash_password(data['password']))
    
    if not set_clauses:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '无更新内容'})
    
    # 防止禁用自己：检查is_active是否从1改为0
    token_for_self_check = request.headers.get('X-Staff-Token', '')
    if 'is_active' in data and data['is_active'] == 0:
        cursor.execute('''
            SELECT staff_id FROM staff_tokens 
            WHERE token = %s AND expires_at::timestamp > NOW()
        ''', (token_for_self_check,))
        token_row = cursor.fetchone()
        if token_row and token_row['staff_id'] == staff_id:
            database.release_connection(conn)
            return jsonify({'success': False, 'message': '不能禁用自己的账号'})
    
    params.append(staff_id)
    query = sql.SQL('UPDATE staff SET {} WHERE id = %s').format(
        sql.SQL(', ').join(set_clauses)
    )
    cursor.execute(query, params)
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

@admin_required
@admin_bp.route('/staff/<int:staff_id>', methods=['DELETE'])
def delete_staff(staff_id):
    """删除员工账号"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'})
    
    conn = database.get_connection()
    cursor = conn.cursor()
    
    # 先清理外键关联数据（equipment_inspection_data.staff_id → staff.id）
    cursor.execute('UPDATE equipment_inspection_data SET staff_id = NULL WHERE staff_id = %s', (staff_id,))
    # 清理 staff_tokens 关联
    cursor.execute('DELETE FROM staff_tokens WHERE staff_id = %s', (staff_id,))
    
    cursor.execute('DELETE FROM staff WHERE id = %s', (staff_id,))
    conn.commit()
    database.release_connection(conn)
    
    return jsonify({'success': True})

# ========== 价格配置 ==========
