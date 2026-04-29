# -*- coding: utf-8 -*-
"""数据管理API路由（Admin使用）- 模块化拆分"""
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from decimal import Decimal
import uuid
import database
import psycopg2
from psycopg2 import sql

admin_bp = Blueprint('admin', __name__)

from auth import admin_required, validate_staff_token, require_admin


@admin_bp.before_request
def _check_admin_auth():
    token = request.headers.get('X-Staff-Token', '')
    if not require_admin(token):
        return jsonify({'success': False, 'message': '需要管理员权限'}), 403


# --- Sub-modules (register routes on import) ---
from . import catalog
from . import services
from . import staff
from . import pricing
from . import customers
from . import backup_restore
from . import maintenance
from . import inventory
