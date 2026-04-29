# -*- coding: utf-8 -*-
"""客户端API路由 - 模块化拆分"""
from flask import Blueprint, request, jsonify, send_file
import database
import json
import os
import base64
from datetime import datetime, timedelta
from pydantic import ValidationError
from validators import (CustomerPhoneLogin, CreateOrder, EditOrder, ExpressUpdate, SpecialServiceRespond)
from psycopg2 import sql
from status_log import log_status_change
import secrets

client_bp = Blueprint('client', __name__)

from auth import validate_customer_token, generate_token
from notification import _integration_hook_notify

# --- Sub-modules (register routes on import) ---
from . import auth
from . import products
from . import client_services
from . import orders
from . import tracking
from . import client_reports
