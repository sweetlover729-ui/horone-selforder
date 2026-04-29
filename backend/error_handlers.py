# -*- coding: utf-8 -*-
"""
统一错误处理模块
提供标准化的错误响应和日志记录
"""

import traceback
import os
from flask import jsonify, request
from logging_config import get_logger

logger = get_logger('error_handlers')

class APIError(Exception):
    """API错误基类"""
    def __init__(self, message, status_code=400, error_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"

def handle_api_error(error):
    """处理APIError"""
    response = {
        'success': False,
        'message': error.message,
        'error_code': error.error_code
    }
    logger.warning(f"APIError: {error.message} (code={error.error_code})")
    return jsonify(response), error.status_code

def handle_generic_error(error):
    """处理通用异常"""
    error_id = f"ERR500_{id(error)}"
    logger.error(f"Unhandled exception [{error_id}]: {str(error)}\n{traceback.format_exc()}")
    
    response = {
        'success': False,
        'message': '服务器内部错误',
        'error_id': error_id,
        'error_code': 'ERR_500'
    }
    
    # 开发环境显示详细错误
    if os.environ.get('FLASK_ENV') == 'development':
        response['detail'] = str(error)
        response['traceback'] = traceback.format_exc()
    
    return jsonify(response), 500

def handle_not_found(error):
    """处理404错误"""
    return jsonify({
        'success': False,
        'message': '请求的资源不存在',
        'error_code': 'ERR_404'
    }), 404

def handle_method_not_allowed(error):
    """处理405错误"""
    return jsonify({
        'success': False,
        'message': '请求方法不允许',
        'error_code': 'ERR_405'
    }), 405

def handle_bad_request(error):
    """处理400错误"""
    return jsonify({
        'success': False,
        'message': '请求参数错误',
        'error_code': 'ERR_400'
    }), 400

def log_request_info():
    """记录请求信息"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

def log_response_info(response):
    """记录响应信息"""
    logger.info(f"{request.method} {request.path} - {response.status_code}")
    return response

# 错误码定义
ERROR_CODES = {
    'ERR_400': '请求参数错误',
    'ERR_401': '未登录或token已过期',
    'ERR_403': '无权访问',
    'ERR_404': '资源不存在',
    'ERR_405': '请求方法不允许',
    'ERR_409': '资源冲突',
    'ERR_422': '请求数据验证失败',
    'ERR_429': '请求过于频繁',
    'ERR_500': '服务器内部错误',
    'ERR_ORDER_001': '订单不存在',
    'ERR_ORDER_002': '订单状态不正确',
    'ERR_ORDER_003': '订单已被其他技术员认领',
    'ERR_AUTH_001': '用户名或密码错误',
    'ERR_AUTH_002': 'token无效',
    'ERR_FILE_001': '文件上传失败',
    'ERR_FILE_002': '文件格式不支持',
    'ERR_FILE_003': '文件过大',
}

def get_error_message(error_code):
    """获取错误码对应的消息"""
    return ERROR_CODES.get(error_code, '未知错误')
