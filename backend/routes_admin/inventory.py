# -*- coding: utf-8 -*-
"""配件库存管理 — CRUD + 入库/出库 + 使用记录"""
from flask import request, jsonify
from psycopg2 import sql
from database import get_connection, release_connection
from auth import validate_staff_token
from status_log import log_status_change

from . import admin_bp  # admin_bp from __init__.py (before_request 已保护)


def _get_staff():
    """获取当前操作用户"""
    token = request.headers.get('X-Staff-Token', '').strip()
    return validate_staff_token(token)


# ═══════════════════ 配件 CRUD ═══════════════════


@admin_bp.route('/parts', methods=['GET'])
def list_parts():
    """配件列表（支持筛选/搜索）"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = get_connection()
    cursor = conn.cursor()

    category = request.args.get('category', '')
    search = request.args.get('search', '')
    brand_id = request.args.get('brand_id', '')
    low_stock = request.args.get('low_stock', '')  # '1' = 只显示低库存

    where_clauses = []
    params = []

    if search:
        where_clauses.append(sql.SQL('(p.name ILIKE %s OR p.part_code ILIKE %s OR p.description ILIKE %s)'))
        like = f'%{search}%'
        params.extend([like, like, like])
    if category:
        where_clauses.append(sql.SQL('p.category = %s'))
        params.append(category)
    if brand_id:
        where_clauses.append(sql.SQL('p.brand_id = %s'))
        params.append(int(brand_id))
    if low_stock == '1':
        where_clauses.append(sql.SQL('p.stock <= p.min_stock'))
    where_clauses.append(sql.SQL('p.is_active = TRUE'))

    where = sql.SQL(' AND ').join(where_clauses) if where_clauses else sql.SQL('TRUE')

    cursor.execute(sql.SQL('''
        SELECT p.*,
               COALESCE(b.name, '') as brand_name,
               COALESCE(m.name, '') as model_name
        FROM parts p
        LEFT JOIN brands b ON b.id = p.brand_id
        LEFT JOIN models m ON m.id = p.model_id
        WHERE {where}
        ORDER BY p.category, p.name
    ''').format(where=where), params)
    parts = cursor.fetchall()

    # 类别列表（用于筛选）
    cursor.execute("SELECT DISTINCT category FROM parts WHERE is_active=TRUE AND category IS NOT NULL AND category != '' ORDER BY category")
    categories = [r['category'] for r in cursor.fetchall()]

    release_connection(conn)
    return jsonify({
        'success': True,
        'data': parts,
        'categories': categories,
        'total': len(parts),
    })


@admin_bp.route('/parts', methods=['POST'])
def create_part():
    """创建配件"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'message': '配件名称不能为空'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql.SQL('''
        INSERT INTO parts (name, part_code, category, description, unit, stock,
                          min_stock, cost_price, selling_price, brand_id, model_id, notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    '''), (
        name,
        data.get('part_code', '').strip() or None,
        data.get('category', '').strip() or None,
        data.get('description', '').strip() or None,
        data.get('unit', '个'),
        data.get('stock', 0),
        data.get('min_stock', 5),
        data.get('cost_price', 0),
        data.get('selling_price', 0),
        data.get('brand_id') or None,
        data.get('model_id') or None,
        data.get('notes', '').strip() or None,
    ))
    pid = cursor.fetchone()['id']

    # 记录初始库存
    if data.get('stock', 0) > 0:
        cursor.execute('''
            INSERT INTO part_stock_log (part_id, change_qty, after_qty, change_type, operator, notes)
            VALUES (%s,%s,%s,'in',%s,'初始化库存')
        ''', (pid, data['stock'], data['stock'], staff['full_name'] or staff['username']))

    conn.commit()
    release_connection(conn)
    return jsonify({'success': True, 'data': {'id': pid}, 'message': '配件已创建'})


@admin_bp.route('/parts/<int:part_id>', methods=['GET'])
def get_part(part_id):
    """配件详情"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM parts WHERE id=%s', (part_id,))
    part = cursor.fetchone()
    release_connection(conn)
    if not part:
        return jsonify({'success': False, 'message': '配件不存在'}), 404
    return jsonify({'success': True, 'data': part})


@admin_bp.route('/parts/<int:part_id>', methods=['PUT'])
def update_part(part_id):
    """更新配件"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.get_json() or {}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM parts WHERE id=%s', (part_id,))
    part = cursor.fetchone()
    if not part:
        release_connection(conn)
        return jsonify({'success': False, 'message': '配件不存在'}), 404

    new_stock = data.get('stock')
    old_stock = part['stock']
    cursor.execute(sql.SQL('''
        UPDATE parts SET
            name=%s, part_code=%s, category=%s, description=%s, unit=%s,
            stock=COALESCE(%s, stock), min_stock=%s,
            cost_price=%s, selling_price=%s,
            brand_id=%s, model_id=%s, notes=%s,
            updated_at=NOW()
        WHERE id=%s
    '''), (
        data.get('name', part['name']),
        data.get('part_code', '').strip() or None,
        data.get('category', '').strip() or None,
        data.get('description', '').strip() or None,
        data.get('unit', part['unit']),
        new_stock,  # None keeps old value
        data.get('min_stock', part['min_stock']),
        data.get('cost_price', part['cost_price']),
        data.get('selling_price', part['selling_price']),
        data.get('brand_id') or None,
        data.get('model_id') or None,
        data.get('notes', '').strip() or None,
        part_id,
    ))

    # 库存变动日志
    if new_stock is not None and int(new_stock) != old_stock:
        diff = int(new_stock) - old_stock
        cursor.execute('''
            INSERT INTO part_stock_log (part_id, change_qty, after_qty, change_type, operator, notes)
            VALUES (%s,%s,%s,'adjust',%s,'手动调整库存')
        ''', (part_id, diff, int(new_stock), staff['full_name'] or staff['username']))

    conn.commit()
    release_connection(conn)
    return jsonify({'success': True, 'message': '配件已更新'})


@admin_bp.route('/parts/<int:part_id>', methods=['DELETE'])
def delete_part(part_id):
    """删除配件（软删除）"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE parts SET is_active=FALSE, updated_at=NOW() WHERE id=%s", (part_id,))
    conn.commit()
    release_connection(conn)
    return jsonify({'success': True, 'message': '配件已删除'})


# ═══════════════════ 库存操作 ═══════════════════


@admin_bp.route('/parts/<int:part_id>/stock-in', methods=['POST'])
def stock_in(part_id):
    """入库"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.get_json() or {}
    qty = data.get('quantity', 0)
    if qty <= 0:
        return jsonify({'success': False, 'message': '入库数量必须大于0'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE parts SET stock=stock+%s, updated_at=NOW() WHERE id=%s RETURNING stock', (qty, part_id))
    row = cursor.fetchone()
    if not row:
        release_connection(conn)
        return jsonify({'success': False, 'message': '配件不存在'}), 404
    after_qty = row['stock']
    cursor.execute('''
        INSERT INTO part_stock_log (part_id, change_qty, after_qty, change_type, operator, notes)
        VALUES (%s,%s,%s,'in',%s,%s)
    ''', (part_id, qty, after_qty, staff['full_name'] or staff['username'], data.get('notes', '')))
    conn.commit()
    release_connection(conn)
    return jsonify({'success': True, 'data': {'stock': after_qty}, 'message': f'入库 {qty}，当前库存 {after_qty}'})


@admin_bp.route('/parts/<int:part_id>/stock-out', methods=['POST'])
def stock_out(part_id):
    """出库/领用（维修使用，不绑定订单）"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    data = request.get_json() or {}
    qty = data.get('quantity', 0)
    order_id = data.get('order_id') or None
    if qty <= 0:
        return jsonify({'success': False, 'message': '出库数量必须大于0'}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT stock FROM parts WHERE id=%s', (part_id,))
    part = cursor.fetchone()
    if not part:
        release_connection(conn)
        return jsonify({'success': False, 'message': '配件不存在'}), 404
    if part['stock'] < qty:
        release_connection(conn)
        return jsonify({'success': False, 'message': f'库存不足，当前 {part["stock"]}，需要 {qty}'}), 400

    cursor.execute('UPDATE parts SET stock=stock-%s, updated_at=NOW() WHERE id=%s RETURNING stock', (qty, part_id))
    after_qty = cursor.fetchone()['stock']

    # 出库日志
    cursor.execute('''
        INSERT INTO part_stock_log (part_id, change_qty, after_qty, change_type, related_order_id, operator, notes)
        VALUES (%s,%s,%s,'out',%s,%s,%s)
    ''', (part_id, -qty, after_qty, order_id, staff['full_name'] or staff['username'],
          data.get('notes', '')))

    # 关联订单使用记录
    if order_id:
        cursor.execute('SELECT selling_price FROM parts WHERE id=%s', (part_id,))
        p = cursor.fetchone()
        unit_price = data.get('unit_price') or p['selling_price'] or 0
        cursor.execute('''
            INSERT INTO part_usage (order_id, part_id, quantity, unit_price, used_by_staff_id, notes)
            VALUES (%s,%s,%s,%s,%s,%s)
        ''', (order_id, part_id, qty, unit_price, staff['id'], data.get('notes', '')))

    conn.commit()
    release_connection(conn)
    return jsonify({'success': True, 'data': {'stock': after_qty}, 'message': f'出库 {qty}，剩余 {after_qty}'})


# ═══════════════════ 统计与日志 ═══════════════════


@admin_bp.route('/parts/low-stock', methods=['GET'])
def low_stock_parts():
    """低库存预警"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.part_code, p.stock, p.min_stock, p.category,
               (p.min_stock - p.stock) as shortage
        FROM parts p
        WHERE p.is_active = TRUE AND p.stock <= p.min_stock
        ORDER BY (p.min_stock - p.stock) DESC
    ''')
    result = cursor.fetchall()
    release_connection(conn)
    return jsonify({'success': True, 'data': result, 'total': len(result)})


@admin_bp.route('/parts/<int:part_id>/stock-log', methods=['GET'])
def part_stock_history(part_id):
    """库存变更历史"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, p.name as part_name
        FROM part_stock_log s
        JOIN parts p ON p.id = s.part_id
        WHERE s.part_id = %s
        ORDER BY s.created_at DESC
        LIMIT 100
    ''', (part_id,))
    result = cursor.fetchall()
    release_connection(conn)
    return jsonify({'success': True, 'data': result, 'total': len(result)})


@admin_bp.route('/parts/usage/<int:order_id>', methods=['GET'])
def order_part_usage(order_id):
    """订单使用的配件列表"""
    staff = _get_staff()
    if not staff:
        return jsonify({'success': False, 'message': '未授权'}), 401
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pu.*, p.name as part_name, p.part_code, p.unit,
               s.full_name as used_by_name
        FROM part_usage pu
        JOIN parts p ON p.id = pu.part_id
        LEFT JOIN staff s ON s.id = pu.used_by_staff_id
        WHERE pu.order_id = %s
        ORDER BY pu.created_at DESC
    ''', (order_id,))
    result = cursor.fetchall()
    release_connection(conn)
    return jsonify({'success': True, 'data': result, 'total': len(result)})

