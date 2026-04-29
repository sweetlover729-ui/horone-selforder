# -*- coding: utf-8 -*-
"""
控制台API路由（员工使用）
"""
from flask import Blueprint, request, jsonify, send_file
import database
import shutil
import json
import os
import base64
from datetime import datetime, timedelta
import secrets
from psycopg2 import sql
from pydantic import ValidationError
from validators import StaffLogin
from logging_config import get_logger

logger = get_logger('routes_console')

console_bp = Blueprint('console', __name__)

from auth import validate_staff_token, generate_token
from notification import _integration_hook_notify, notify_ship

from status_log import log_status_change  # noqa: F401  re-exported for sub-modules


def save_base64_image(base64_data, order_id, node_id=None):
    """保存base64图片到节点的photos目录"""
    try:
        # 解析base64
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]

        image_data = base64.b64decode(base64_data)

        # 验证文件内容是否为合法图片（magic bytes 检查）
        _IMAGE_SIGNATURES = {
            b'\xff\xd8\xff': 'jpg',
            b'\x89PNG': 'png',
            b'RIFF': 'webp',  # WebP 以 RIFF 开头
        }
        ext = None
        for sig, fmt in _IMAGE_SIGNATURES.items():
            if image_data[:len(sig)] == sig:
                ext = fmt
                break
        if ext is None:
            logger.warning("保存图片失败: 非法文件格式 (前4字节: %s)", image_data[:4].hex())
            return None

        # 创建目录：/uploads/orders/{order_id}/nodes/{node_id}/
        node_dir = f"{database.ORDER_UPLOAD_DIR}/{order_id}/nodes"
        if node_id:
            node_dir = f"{node_dir}/{node_id}"
        os.makedirs(node_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        file_path = os.path.join(node_dir, f"{timestamp}.{ext}")

        with open(file_path, 'wb') as f:
            f.write(image_data)

        # 返回相对于 uploads/ 的路径（不含 /uploads/ 前缀）
        relative = f"orders/{order_id}/nodes"
        if node_id:
            relative = f"{relative}/{node_id}"
        relative = f"{relative}/{os.path.basename(file_path)}"
        return relative
    except Exception as e:
        logger.error("保存图片失败: %s", e)
        return None

# ========== 认证 ==========

# --- Route handler sub-modules (registered on import) ---
from . import auth
from . import orders
from . import workflow
from . import reports
from . import simulate
