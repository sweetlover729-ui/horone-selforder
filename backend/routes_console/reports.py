# -*- coding: utf-8 -*-
"""Console API — Dashboard, reports, photos, PDF"""

from flask import request, jsonify
import database
import json
import os
from datetime import datetime, timedelta
from psycopg2 import sql
from logging_config import get_logger
from flask import send_file
import base64
from auth import validate_staff_token, admin_required

from . import console_bp
from . import log_status_change
from . import save_base64_image

logger = get_logger('routes_console.reports')


@console_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    conn = database.get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().strftime('%Y-%m-01')

    # 待处理订单数
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'")
    pending_count = cursor.fetchone()['count']

    # 维修中订单数
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status IN ('received', 'inspecting', 'repairing')")
    repairing_count = cursor.fetchone()['count']

    # 今日订单数
    cursor.execute("SELECT COUNT(*) as count FROM orders WHERE date(created_at) = %s AND status != 'deleted'", (today,))
    today_orders = cursor.fetchone()['count']

    # 本月收入
    cursor.execute('''
        SELECT COALESCE(SUM(total_amount), 0) as revenue
        FROM orders
        WHERE date(created_at) >= %s AND status NOT IN ('cancelled', 'deleted')
    ''', (month_start,))
    month_revenue = cursor.fetchone()['revenue']

    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {
            'pending_count': pending_count,
            'repairing_count': repairing_count,
            'today_orders': today_orders,
            'month_revenue': month_revenue
        }
    })



@console_bp.route('/dashboard/report', methods=['GET'])
def get_dashboard_report():
    """获取统计报表数据"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或token已过期'})

    start_date = request.args.get('startDate', '')
    end_date = request.args.get('endDate', '')
    product_type_id = request.args.get('product_type_id', '', type=int) or None
    brand_id = request.args.get('brand_id', '', type=int) or None
    model_id = request.args.get('model_id', '', type=int) or None
    service_type_id = request.args.get('service_type_id', '', type=int) or None
    customer_id = request.args.get('customer_id', '', type=int) or None

    conn = database.get_connection()
    cursor = conn.cursor()

    # 构建 WHERE 子句
    conditions = ["status != 'deleted'"]
    params = []
    if start_date:
        conditions.append("o.created_at >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("o.created_at <= %s")
        params.append(end_date + ' 23:59:59')
    if product_type_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE product_type_id = %s)")
        params.append(product_type_id)
    if brand_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE brand_id = %s)")
        params.append(brand_id)
    if model_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE model_id = %s)")
        params.append(model_id)
    if service_type_id:
        conditions.append("o.id IN (SELECT DISTINCT order_id FROM order_items WHERE service_type_id = %s)")
        params.append(service_type_id)
    if customer_id:
        conditions.append("o.customer_id = %s")
        params.append(customer_id)
    where = "WHERE " + " AND ".join(conditions)

    # 子查询用的 WHERE（包含日期和客户筛选，不含 order_items 级联）
    sub_where_conditions = ["o.status != 'deleted'"]
    sub_where_params = []
    if start_date:
        sub_where_conditions.append("o.created_at >= %s")
        sub_where_params.append(start_date)
    if end_date:
        sub_where_conditions.append("o.created_at <= %s")
        sub_where_params.append(end_date + ' 23:59:59')
    if customer_id:
        sub_where_conditions.append("o.customer_id = %s")
        sub_where_params.append(customer_id)
    sub_where = "WHERE " + " AND ".join(sub_where_conditions)

    # 级联筛选条件
    # cascade_conditions_oi: 带表别名（用于 FROM order_items oi 的 breakdown 查询）
    # cascade_conditions_plain: 不带别名（用于子查询 SELECT ... FROM order_items WHERE ...）
    cascade_conditions_oi = []
    cascade_conditions_plain = []
    cascade_params = []
    if product_type_id:
        cascade_conditions_oi.append("oi.product_type_id = %s")
        cascade_conditions_plain.append("product_type_id = %s")
        cascade_params.append(product_type_id)
    if brand_id:
        cascade_conditions_oi.append("oi.brand_id = %s")
        cascade_conditions_plain.append("brand_id = %s")
        cascade_params.append(brand_id)
    if model_id:
        cascade_conditions_oi.append("oi.model_id = %s")
        cascade_conditions_plain.append("model_id = %s")
        cascade_params.append(model_id)
    if service_type_id:
        cascade_conditions_oi.append("oi.service_type_id = %s")
        cascade_conditions_plain.append("service_type_id = %s")
        cascade_params.append(service_type_id)

    def build_oi_where():
        """构建 order_items JOIN 过滤（带 oi. 别名，用于 breakdown 查询）"""
        if cascade_conditions_oi:
            return "AND oi.order_id IN (SELECT DISTINCT order_id FROM order_items WHERE " + " AND ".join(cascade_conditions_plain) + ")"
        return ""

    def build_sub_filter():
        """构建子查询过滤（不带别名，用于 total/staff/monthly 等子查询）"""
        if cascade_conditions_plain:
            return " AND o.id IN (SELECT DISTINCT order_id FROM order_items WHERE " + " AND ".join(cascade_conditions_plain) + ")"
        return ""

    oi_filter = build_oi_where()
    oi_params = cascade_params[:]  # cascade params for order_items subquery
    # breakdown 查询参数 = sub_where 参数 + oi_filter 参数
    breakdown_params = list(sub_where_params) + list(cascade_params)

    # 总订单数和总收入（包含级联筛选）
    total_where = where
    total_params = list(params)
    total_where += build_sub_filter()
    total_params.extend(cascade_params)
    cursor.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as rev FROM orders o " + total_where, total_params)
    row = cursor.fetchone()
    total_orders = row['cnt']
    total_revenue = row['rev']

    # 状态分布（包含级联筛选）
    cursor.execute("SELECT status, COUNT(*) as cnt FROM orders o " + total_where + " GROUP BY status", total_params)
    status_breakdown = {r['status']: r['cnt'] for r in cursor.fetchall()}

    # 已完成数（用于计算完成率）
    completed_count = status_breakdown.get('completed', 0)

    # 产品类型分布
    pt_sql = '''
        SELECT pt.name, COUNT(DISTINCT oi.order_id) as cnt, COALESCE(SUM(o.total_amount), 0) as rev
        FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.id
        LEFT JOIN product_types pt ON oi.product_type_id = pt.id
        ''' + sub_where + '\n        ' + oi_filter + '''
        GROUP BY pt.name ORDER BY cnt DESC
    '''
    cursor.execute(pt_sql, breakdown_params)
    product_type_breakdown = [{'name': r['name'] or '未分类', 'count': r['cnt'], 'revenue': round(r['rev'] or 0, 2)} for r in cursor.fetchall()]

    # 品牌分布
    brand_sql = '''
        SELECT b.name, COUNT(DISTINCT oi.order_id) as cnt, COALESCE(SUM(o.total_amount), 0) as rev
        FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.id
        LEFT JOIN brands b ON oi.brand_id = b.id
        ''' + sub_where + '\n        ' + oi_filter + '''
        GROUP BY b.name ORDER BY cnt DESC
    '''
    cursor.execute(brand_sql, breakdown_params)
    brand_breakdown = [{'name': r['name'] or '未分类', 'count': r['cnt'], 'revenue': round(r['rev'] or 0, 2)} for r in cursor.fetchall()]

    # 服务类型分布
    st_sql = '''
        SELECT st.name, COUNT(DISTINCT oi.order_id) as cnt, COALESCE(SUM(o.total_amount), 0) as rev
        FROM order_items oi
        LEFT JOIN orders o ON oi.order_id = o.id
        LEFT JOIN service_types st ON oi.service_type_id = st.id
        ''' + sub_where + '\n        ' + oi_filter + '''
        GROUP BY st.name ORDER BY cnt DESC
    '''
    cursor.execute(st_sql, breakdown_params)
    service_type_breakdown = [{'name': r['name'] or '未分类', 'count': r['cnt'], 'revenue': round(r['rev'] or 0, 2)} for r in cursor.fetchall()]

    # 技师业绩（按领取订单的技师 assigned_staff_id 统计）
    staff_where = "WHERE o.status != 'deleted' AND o.assigned_staff_id IS NOT NULL"
    staff_params = []
    if start_date:
        staff_where += " AND o.created_at >= %s"
        staff_params.append(start_date)
    if end_date:
        staff_where += " AND o.created_at <= %s"
        staff_params.append(end_date + ' 23:59:59')
    if cascade_conditions_plain:
        staff_where += " AND o.id IN (SELECT DISTINCT order_id FROM order_items WHERE " + " AND ".join(cascade_conditions_plain) + ")"
        staff_params.extend(cascade_params)
    if customer_id:
        staff_where += " AND o.customer_id = %s"
        staff_params.append(customer_id)
    staff_sql = '''
        SELECT COALESCE(s.full_name, '未分配') as name,
               COUNT(o.id) as cnt,
               COALESCE(SUM(o.total_amount), 0) as rev
        FROM orders o
        LEFT JOIN staff s ON o.assigned_staff_id = s.id
        ''' + staff_where + '''
        GROUP BY s.full_name ORDER BY rev DESC
    '''
    cursor.execute(staff_sql, staff_params)
    staff_breakdown = [{'name': r['name'], 'count': r['cnt'], 'revenue': round(r['rev'] or 0, 2)} for r in cursor.fetchall()]

    # 月度趋势（复用主 WHERE + 级联筛选）
    monthly_where = where
    monthly_params = list(params)
    if cascade_conditions_plain:
        monthly_where += " AND o.id IN (SELECT DISTINCT order_id FROM order_items WHERE " + " AND ".join(cascade_conditions_plain) + ")"
        monthly_params.extend(cascade_params)
    if customer_id:
        monthly_where += " AND o.customer_id = %s"
        monthly_params.append(customer_id)
    monthly_sql = '''
        SELECT TO_CHAR(o.created_at, 'YYYY-MM') as month,
               COUNT(*) as cnt, COALESCE(SUM(total_amount), 0) as rev
        FROM orders o
        ''' + monthly_where + '''
        GROUP BY month ORDER BY month DESC
    '''
    cursor.execute(monthly_sql, monthly_params)
    monthly_trend = [{'month': r['month'], 'count': r['cnt'], 'revenue': round(r['rev'] or 0, 2)} for r in cursor.fetchall()]

    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {
            'total_orders': total_orders,
            'total_revenue': round(total_revenue, 2),
            'avg_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            'completion_rate': round(completed_count / total_orders * 100, 1) if total_orders > 0 else 0,
            'status_breakdown': status_breakdown,
            'product_type_breakdown': product_type_breakdown,
            'brand_breakdown': brand_breakdown,
            'service_type_breakdown': service_type_breakdown,
            'staff_breakdown': staff_breakdown,
            'monthly_trend': monthly_trend
        }
    })

@console_bp.route('/orders/<int:order_id>/nodes/<int:node_id>/photo', methods=['POST'])
def upload_node_photo(order_id, node_id):
    """上传节点照片（维修员操作）"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或无权限'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()

    # 验证节点属于该订单
    cursor.execute('SELECT id, photos FROM tracking_nodes WHERE id = %s AND order_id = %s', (node_id, order_id))
    node = cursor.fetchone()
    if not node:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '节点不存在'}), 404

    # 处理上传的文件
    if 'photos' not in request.files:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '请上传照片'}), 400

    files = request.files.getlist('photos')
    if not files:
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': '请选择至少一张照片'}), 400  # pragma: no cover

    # 保存目录
    photo_dir = f'{database.ORDER_UPLOAD_DIR}/{order_id}/nodes/{node_id}'
    os.makedirs(photo_dir, exist_ok=True)

    # 解析现有photos JSON
    try:
        existing_photos = json.loads(node['photos']) if node['photos'] else []
    except (json.JSONDecodeError, TypeError, ValueError):  # pragma: no cover
        existing_photos = []  # pragma: no cover

    import uuid
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB per file
    saved_files = []
    for f in files[:9]:  # 最多9张
        if not f.filename:
            continue  # pragma: no cover
        # 文件大小限制
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > MAX_FILE_SIZE:
            continue  # pragma: no cover
        ext = os.path.splitext(f.filename)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
            continue  # pragma: no cover
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        filepath = os.path.join(photo_dir, filename)
        f.save(filepath)
        saved_files.append(filename)
        existing_photos.append(filename)

    if not saved_files:
        database.release_connection(conn)  # pragma: no cover
        return jsonify({'success': False, 'message': '没有有效的图片文件'}), 400  # pragma: no cover

    # 更新数据库
    cursor.execute('UPDATE tracking_nodes SET photos = %s WHERE id = %s',
                   (json.dumps(existing_photos, ensure_ascii=False), node_id))
    conn.commit()
    database.release_connection(conn)

    return jsonify({
        'success': True,
        'data': {
            'node_id': node_id,
            'added': len(saved_files),
            'photos': existing_photos
        }
    })

@console_bp.route('/orders/<int:order_id>/nodes/<int:node_id>/photo/<filename>', methods=['GET'])
def get_node_photo(order_id, node_id, filename):
    """获取节点照片"""
    token = request.headers.get('X-Staff-Token', '') or request.args.get('token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401

    # 数据库存储路径: orders/{order_id}/nodes/{node_id}/{filename}
    # 相对于 UPLOAD_DIR，所以完整路径是 UPLOAD_DIR + 数据库存储路径
    filepath = f'{database.UPLOAD_DIR}/orders/{order_id}/nodes/{node_id}/{filename}'
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '照片不存在'}), 404

    return send_file(filepath)  # pragma: no cover

@console_bp.route('/orders/<int:order_id>/generate-report', methods=['POST'])
def generate_report(order_id):
    """手动生成维修报告PDF"""
    token = request.headers.get('X-Staff-Token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录或无权限'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    if not order:
        database.release_connection(conn)
        return jsonify({'success': False, 'message': '订单不存在'}), 404

    from pdf_generator import generate_order_pdf
    pdf_path = generate_order_pdf(order)
    database.release_connection(conn)

    if pdf_path:
        return jsonify({'success': True, 'data': {'pdf_path': pdf_path}})
    else:
        return jsonify({'success': False, 'message': 'PDF生成失败'}), 500

@console_bp.route('/orders/<int:order_id>/report-pdf', methods=['GET'])
def get_report_pdf(order_id):
    """管理员查看/下载报告PDF"""
    token = request.headers.get('X-Staff-Token', '') or request.args.get('token', '')
    staff = validate_staff_token(token)
    if not staff:
        return jsonify({'success': False, 'message': '未登录'}), 401

    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT pdf_path, order_no FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    database.release_connection(conn)

    if not order or not order['pdf_path']:
        return jsonify({'success': False, 'message': '报告未生成'}), 404

    if not os.path.exists(order['pdf_path']):
        return jsonify({'success': False, 'message': '报告文件已归档，请联系管理员'}), 410  # pragma: no cover

    # 支持预览(inline)和下载(attachment)两种模式
    as_download = request.args.get('download', '0') == '1'
    response = send_file(
        order['pdf_path'],
        as_attachment=as_download,
        download_name=f"{order['order_no']}.pdf" if as_download else None,
        mimetype='application/pdf'
    )
    # 添加响应头防止 Cloudflare 缓存/优化
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Length'] = str(os.path.getsize(order['pdf_path']))
    return response


