"""
结构化日志模块 - JSON格式、请求追踪、分级输出

用法：
    from logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("something happened", extra={"order_id": 123})

请求上下文自动附加 req_id / method / path / remote。
"""
import logging
import json
import time
import uuid
import os
from datetime import datetime, timezone
from flask import request, g, has_request_context


class JsonFormatter(logging.Formatter):
    """JSON 格式日志，带请求上下文。"""
    def format(self, record):
        log_entry = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "module": record.name,
            "msg": record.getMessage(),
        }
        if has_request_context():
            log_entry["req_id"] = getattr(g, "request_id", "-")
            log_entry["method"] = request.method
            log_entry["path"] = request.path
            log_entry["remote"] = request.remote_addr
        if record.exc_info and record.exc_info[1]:
            log_entry["exc"] = str(record.exc_info[1])
        # 支持 extra={} 注入自定义字段
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name=None):
    """获取 horone 命名空间下的 logger。
    
    - get_logger(__name__)  →  horone.backend.routes_console
    - get_logger('db')      →  horone.db
    """
    if name:
        # 去掉项目路径前缀，统一为 horone.xxx
        if name.startswith('backend.'):
            name = name[len('backend.'):]
        logger_name = f"horone.{name}"
    else:
        logger_name = "horone"
    return logging.getLogger(logger_name)

def init_logging(app):
    """初始化结构化日志：替换 Flask 默认 handler，挂载请求追踪中间件。
    
    调用位置：app.py 中 create_app() 或模块顶部，且必须在 register_blueprint 之前。
    """
    log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'), logging.INFO)

    # Root handler：JSON 格式输出到 stderr
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    # 替换 Flask 默认 handler
    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(log_level)

    # 抑制 gunicorn 重复日志
    logging.getLogger("gunicorn.error").handlers = []

    # ═══ 请求追踪中间件 ═══
    @app.before_request
    def assign_request_id():
        g.request_id = str(uuid.uuid4())[:8]
        g.start_time = time.time()

    @app.after_request
    def log_response(response):
        if request.path == "/health":
            return response
        elapsed_ms = int((time.time() - g.start_time) * 1000)
        app.logger.info(
            f"{request.method} {request.path} → {response.status_code} "
            f"{elapsed_ms}ms {response.content_length or '-'}B"
        )
        return response
