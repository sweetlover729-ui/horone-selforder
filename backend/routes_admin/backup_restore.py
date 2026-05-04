# -*- coding: utf-8 -*-
"""数据备份与恢复 (backup, restore, archive cleanup)"""
from . import admin_bp
from auth import admin_required, validate_staff_token
import database
from psycopg2 import sql
from flask import request, jsonify, Response as FlaskResponse
from datetime import datetime, date
from decimal import Decimal
import uuid
import json as _json
import os, shutil



# ── 数据备份与恢复 ──────────────────────────────────────────────

BACKUP_TABLES = [
    'product_types', 'brands', 'models', 'service_types', 'service_items',
    'special_services', 'price_overrides',
    'orders', 'order_items', 'tracking_nodes', 'equipment_inspection_data',
    'special_service_records',
    'customers', 'customer_addresses',
    'staff',
]

# 导出时按依赖顺序排列（先导入被依赖的表）
RESTORE_ORDER = [
    'product_types', 'brands', 'models', 'service_types', 'service_items',
    'special_services', 'price_overrides',
    'staff',
    'customers', 'customer_addresses',
    'orders', 'order_items', 'tracking_nodes', 'equipment_inspection_data',
    'special_service_records',
]

# 恢复白名单：每张表允许的列名（防止 JSON 注入）
RESTORE_COLUMN_WHITELIST = {
    'product_types': {'id', 'name', 'categories', 'created_at', 'updated_at'},
    'brands': {'id', 'name', 'product_type_id', 'surcharge', 'created_at', 'updated_at'},
    'models': {'id', 'name', 'brand_id', 'category', 'created_at', 'updated_at'},
    'service_types': {'id', 'name', 'base_price', 'product_type_id', 'category_id', 'created_at', 'updated_at'},
    'service_items': {'id', 'name', 'description', 'service_type_id', 'product_type_id', 'created_at', 'updated_at'},
    'special_services': {'id', 'name', 'price', 'description', 'created_at', 'updated_at'},
    'price_overrides': {'id', 'product_type_id', 'brand_id', 'model_id', 'service_type_id', 'category', 'override_price', 'discount_rate', 'created_at', 'updated_at'},
    'staff': {'id', 'username', 'full_name', 'password_hash', 'role', 'phone', 'is_active', 'created_at', 'updated_at'},
    'customers': {'id', 'nickname', 'name', 'phone', 'openid', 'created_at', 'updated_at'},
    'customer_addresses': {'id', 'customer_id', 'province', 'city', 'district', 'detail', 'contact_name', 'contact_phone', 'is_default', 'created_at', 'updated_at'},
    'orders': {'id', 'order_no', 'customer_id', 'assigned_staff_id', 'status', 'payment_status', 'total_amount', 'freight_amount', 'urgent_fee', 'urgent_service', 'customer_remark', 'express_company', 'express_no', 'return_express_company', 'return_express_no', 'created_at', 'updated_at', 'completed_at'},
    'order_items': {'id', 'order_id', 'product_type_id', 'brand_id', 'model_id', 'service_type_id', 'category', 'quantity', 'item_price', 'final_price', 'brand_name_text', 'model_name_text', 'service_name_text', 'customer_note', 'created_at', 'updated_at'},
    'tracking_nodes': {'id', 'order_id', 'node_code', 'node_name', 'description', 'staff_id', 'staff_name', 'operate_time', 'operate_note', 'photos', 'created_at', 'updated_at'},
    'equipment_inspection_data': {'id', 'order_id', 'staff_id', 'first_stage_serials', 'first_stage_pre_pressure', 'first_stage_post_pressure', 'second_stage_serials', 'second_stage_pre_resistance', 'second_stage_post_resistance', 'created_at', 'updated_at'},
    'special_service_records': {'id', 'order_id', 'special_service_id', 'name', 'price', 'quantity', 'description', 'photos', 'created_at', 'updated_at'},
}

# 恢复时允许的最大字符串长度（防止超大数据攻击）
RESTORE_MAX_TEXT_LEN = 50000

# 敏感列：备份时替换为占位符
SENSITIVE_COLUMNS = {
    'staff': ['password_hash'],
}

# 需要序列化处理的列（text[] 类型）
ARRAY_COLUMNS = {
    'service_items': ['description'],
    'equipment_inspection_data': [
        'first_stage_serials', 'first_stage_pre_pressure', 'first_stage_post_pressure',
        'second_stage_serials', 'second_stage_pre_resistance', 'second_stage_post_resistance',
    ],
    'tracking_nodes': ['photos'],
}


@admin_required
@admin_bp.route('/backup', methods=['GET'])
def export_backup():
    """导出全库数据为 JSON"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'}), 401  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()
    backup_data = {}
    for table in BACKUP_TABLES:
        try:
            cursor.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(table)))
            rows = cursor.fetchall()
            # 将 RealDictRow 转为普通 dict，处理特殊类型
            serialized = []
            array_cols = ARRAY_COLUMNS.get(table, [])
            for row in rows:
                d = {}
                for k, v in dict(row).items():
                    if v is None:
                        d[k] = None
                    elif isinstance(v, (list,)) and k in array_cols:
                        d[k] = list(v)  # PostgreSQL text[] → Python list  # pragma: no cover
                    elif isinstance(v, datetime):
                        d[k] = v.isoformat()
                    elif isinstance(v, date):
                        d[k] = v.isoformat()  # pragma: no cover
                    elif isinstance(v, Decimal):
                        d[k] = float(v)  # pragma: no cover
                    elif isinstance(v, uuid.UUID):
                        d[k] = str(v)  # pragma: no cover
                    else:
                        d[k] = v
                serialized.append(d)
            # Mask sensitive columns (e.g. password_hash)
            sensitive_cols = SENSITIVE_COLUMNS.get(table, [])
            for d in serialized:
                for sc in sensitive_cols:
                    if sc in d:
                        d[sc] = '***REDACTED***'
            backup_data[table] = serialized
        except Exception as e:  # pragma: no cover
            backup_data[table] = {'_error': str(e)}  # pragma: no cover
    database.release_connection(conn)

    from flask import Response as FlaskResponse
    import json as _json
    payload = _json.dumps({
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'tables': backup_data
    }, ensure_ascii=False, default=str)
    return FlaskResponse(payload, mimetype='application/json',
                         headers={'Content-Disposition':
                                  f'attachment; filename=selforder_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'})


@admin_required
@admin_bp.route('/backup/restore', methods=['POST'])
def restore_backup():
    """从 JSON 备份恢复数据（全量覆盖，危险操作）"""
    token = request.headers.get('X-Staff-Token', '')
    if not validate_staff_token(token, allow_inactive=True):
        return jsonify({'success': False, 'message': '未登录或无权限'}), 401  # pragma: no cover

    data = request.get_json(force=True)
    confirm = data.get('confirm', False)
    if not confirm:
        return jsonify({'success': False, 'message': '需要确认参数 confirm=true'}), 400

    tables_data = data.get('tables', {})
    if not tables_data:
        return jsonify({'success': False, 'message': '备份数据为空'}), 400

    conn = database.get_connection()
    cursor = conn.cursor()
    results = {}

    try:
        # 1. 禁用外键约束
        cursor.execute('SET CONSTRAINTS ALL DEFERRED')

        # 2. 按依赖顺序清空 + 导入
        for table in RESTORE_ORDER:
            if table not in tables_data:
                continue
            rows = tables_data[table]
            if isinstance(rows, dict) and '_error' in rows:
                continue  # pragma: no cover
            if not rows:
                continue

            # 清空表
            cursor.execute(sql.SQL('TRUNCATE TABLE {} CASCADE').format(
                sql.Identifier(table)
            ))

            # 获取列名，按白名单过滤
            allowed_cols = RESTORE_COLUMN_WHITELIST.get(table, set())
            columns = [c for c in rows[0].keys() if c in allowed_cols]
            if not columns:
                continue

            # 重置序列
            cursor.execute(sql.SQL("""
                SELECT setval(pg_get_serial_sequence({lit}, 'id'),
                             COALESCE((SELECT MAX(id) FROM {tbl}), 1))
            """).format(
                lit=sql.Literal(table),
                tbl=sql.Identifier(table)
            ))

            inserted = 0
            for row in rows:
                values = []
                for col in columns:
                    val = row.get(col)
                    # 数组列需要转回 PostgreSQL 数组格式
                    if col in ARRAY_COLUMNS.get(table, []) and isinstance(val, list):
                        values.append(val)  # psycopg2 自动处理 Python list → text[]  # pragma: no cover
                    elif isinstance(val, str) and len(val) > RESTORE_MAX_TEXT_LEN:
                        values.append(val[:RESTORE_MAX_TEXT_LEN])  # 截断超长文本
                    else:
                        values.append(val)
                try:
                    cursor.execute(
                        sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
                            sql.Identifier(table),
                            sql.SQL(', ').join([sql.Identifier(c) for c in columns]),
                            sql.SQL(', ').join([sql.Placeholder()] * len(columns))
                        ),
                        values
                    )
                    inserted += 1
                except Exception as e:  # pragma: no cover
                    results.setdefault(table, {'errors': []})  # pragma: no cover
                    results[table].setdefault('errors', []).append(str(e))  # pragma: no cover

            # 重置序列到刚插入的最大 ID
            cursor.execute(sql.SQL("""
                SELECT setval(pg_get_serial_sequence({lit}, 'id'),
                             COALESCE((SELECT MAX(id) FROM {tbl}), 1))
            """).format(
                lit=sql.Literal(table),
                tbl=sql.Identifier(table)
            ))
            results[table] = {'imported': inserted}

        conn.commit()
    except Exception as e:  # pragma: no cover
        conn.rollback()  # pragma: no cover
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': f'恢复失败: {str(e)}', 'results': results}), 500  # pragma: no cover

    database.release_connection(conn)
    return jsonify({'success': True, 'message': '数据恢复完成', 'results': results})


# ========== 归档清理(15天自动清理) ============
@admin_required
@admin_bp.route('/archive-cleanup', methods=['POST'])
def archive_cleanup():
    """归档清理(仅管理员):完成15天后的订单,清理照片、追踪文字描述,只保留基本记录和无图PDF"""
    import os, shutil
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token, allow_inactive=True)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或无权限'}), 401  # pragma: no cover
    if staff.get('role') != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可执行归档'}), 403  # pragma: no cover

    conn = database.get_connection()
    cursor = conn.cursor()

    # 查找完成超过15天的订单
    cursor.execute('''
        SELECT id, order_no, pdf_path FROM orders
        WHERE status = 'completed'
        AND completed_at IS NOT NULL
        AND archived = 0
        AND completed_at + INTERVAL '15 days' < NOW()
    ''')

    orders_to_archive = cursor.fetchall()
    cleaned_count = 0

    for order in orders_to_archive:
        order_id = order['id']

        # 清理追踪节点中的照片和文字描述
        cursor.execute('''
            UPDATE tracking_nodes
            SET photos = '[]', description = '', operate_note = ''
            WHERE order_id = %s
        ''', (order_id,))

        # 清理专项服务照片
        cursor.execute('''
            UPDATE special_service_records
            SET staff_photos = '[]', description = '', staff_note = ''
            WHERE order_id = %s
        ''', (order_id,))

        # 删除本地照片文件(如果有)
        photos_dir = f'{database.ORDER_UPLOAD_DIR}/{order_id}'
        if os.path.exists(photos_dir):
            try:  # pragma: no cover
                shutil.rmtree(photos_dir)  # pragma: no cover
            except OSError:  # pragma: no cover
                pass  # pragma: no cover

        # 标记为已归档
        cursor.execute('UPDATE orders SET archived = 1, updated_at = NOW() WHERE id = %s', (order_id,))
        cleaned_count += 1

    conn.commit()
    database.release_connection(conn)

    return jsonify({
        'success': True,
        'message': f'归档完成,共处理 {cleaned_count} 个订单'
    })
