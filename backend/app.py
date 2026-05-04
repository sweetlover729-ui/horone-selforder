# -*- coding: utf-8 -*-
"""
皓壹调节器维修保养自助下单平台 - 后端主入口
"""
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
from routes_client import client_bp
from routes_console import console_bp
from routes_admin import admin_bp
from token_cleaner import start_cleaner
from backup_scheduler import start_backup_scheduler
from maintenance_reminder import start_reminder_daemon
from error_handlers import (
    handle_api_error, handle_generic_error, handle_not_found,
    handle_method_not_allowed, handle_bad_request
)
from logging_config import init_logging, get_logger

logger = get_logger('app')

# 创建Flask应用（模块级别，供gunicorn使用）
app = Flask(__name__)

# 配置CORS - 白名单
CORS_ORIGINS = [
    'https://horone.alautoai.cn',
    'https://www.horone.alautoai.cn',
    'http://192.168.3.24:3001',   # 内网调试
    'http://localhost:5173',       # Vite dev server
    'http://localhost:3000',       # 本地前端
]
CORS(app, resources={r"/api/*": {"origins": CORS_ORIGINS}})

# REST API 使用 Token 认证，无 Cookie-based session，无需 CSRF 保护
# 全局文件上传大小限制（50MB，超过此值Flask直接拒绝请求）
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# 注册蓝图
app.register_blueprint(client_bp, url_prefix='/api/v1/client')
app.register_blueprint(console_bp, url_prefix='/api/v1/console')
app.register_blueprint(admin_bp, url_prefix='/api/v1/console/admin')

# 错误处理
app.errorhandler(404)(handle_not_found)
app.errorhandler(405)(handle_method_not_allowed)
app.errorhandler(400)(handle_bad_request)
app.errorhandler(500)(handle_generic_error)

# 结构化日志初始化（JSON格式，请求追踪中间件，替代旧log_request/log_response）
init_logging(app)

# 错误处理

# 启动后台token自动清理（守护线程，站点24h在线时自动执行）
start_cleaner(app)
start_backup_scheduler(app)
start_reminder_daemon(app)

# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查 — 含DB连接验证"""
    db_ok = False
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        database.release_connection(conn)
        db_ok = True
    except Exception as e:
        db_error = str(e)
    
    status = {
        'success': db_ok,
        'service': 'horone.selforder',
        'database': 'ok' if db_ok else f'error: {db_error}',
        'timestamp': datetime.now().isoformat()
    }
    return jsonify(status), 200 if db_ok else 503

# 根路径
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'success': True,
        'message': '皓壹调节器维修保养自助下单平台 API',
        'version': '1.0.0',
        'endpoints': {
            'client': '/api/v1/client',
            'console': '/api/v1/console',
            'admin': '/api/v1/console/admin',
            'health': '/health'
        }
    })

def create_app():
    """创建Flask应用（工厂函数，兼容旧代码）"""
    return app

def init_app():
    """初始化应用"""
    logger.info("=" * 50)
    logger.info("皓壹调节器维修保养自助下单平台")
    logger.info("=" * 50)
    
    # 确保上传目录存在
    upload_dirs = [
        database.UPLOAD_DIR,
        database.ORDER_UPLOAD_DIR,
        database.PDF_DIR,
    ]
    for d in upload_dirs:
        os.makedirs(d, exist_ok=True)
        logger.info("目录检查: %s", d)
    
    # 初始化数据库
    logger.info("初始化数据库...")
    database.check_and_init()
    
    logger.info("初始化完成，启动服务...")

if __name__ == '__main__':
    init_app()  # pragma: no cover
    app = create_app()  # pragma: no cover
    logger.info("服务启动成功 - http://localhost:3001")  # pragma: no cover
      # pragma: no cover
    import os  # pragma: no cover
    os.environ['FLASK_ENV'] = 'production'  # pragma: no cover
    app.run(host='0.0.0.0', port=3001, debug=False,  # pragma: no cover
            use_reloader=False, threaded=True)
