# -*- coding: utf-8 -*-
"""
通知系统模块 — 支持微信模板消息 / 短信 / Webhook 多渠道推送

当前实现：基础设施层（非阻塞线程池 + 可配置渠道 + 模板引擎）
微信 API 密钥 / 短信 AK 配置后立即生效
"""
import os
import json
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any
from logging_config import get_logger

logger = get_logger('notification')

import requests

# ── 配置 ──────────────────────────────────────────────
# 微信公众平台
WECHAT_APPID = os.getenv('NOTIFY_WECHAT_APPID', '')
WECHAT_APPSECRET = os.getenv('NOTIFY_WECHAT_APPSECRET', '')
WECHAT_TOKEN_URL = 'https://api.weixin.qq.com/cgi-bin/token'
WECHAT_MSG_URL = 'https://api.weixin.qq.com/cgi-bin/message/template/send'

# 短信（预留接口）
SMS_PROVIDER = os.getenv('NOTIFY_SMS_PROVIDER', '')        # aliyun | tencent
SMS_ACCESS_KEY = os.getenv('NOTIFY_SMS_ACCESS_KEY', '')
SMS_TEMPLATE_ID = os.getenv('NOTIFY_SMS_TEMPLATE_ID', '')

# 通用 Webhook
WEBHOOK_URL = os.getenv('NOTIFY_WEBHOOK_URL', '')

# 全局开关
NOTIFICATION_ENABLED = os.getenv('NOTIFY_ENABLED', 'true').lower() in ('1', 'true', 'yes')
MAX_RETRIES = 2

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='notify-')
_access_token: str = ''
_access_token_expiry: float = 0.0
_lock = threading.Lock()


# ── 状态 → 通知模板 ────────────────────────────────────

STATUS_TEMPLATES: Dict[str, Dict[str, str]] = {
    'received': {
        'title': '订单已接收',
        'body': '您的维修订单 {order_no} 已由技师接单，即将进入检测流程。',
        'remark': '点击查看订单详情',
    },
    'inspecting': {
        'title': '设备检测中',
        'body': '订单 {order_no} 正在拆件检测，技师将评估设备状况。',
        'remark': '检测完成后将进入维修环节',
    },
    'repairing': {
        'title': '维修进行中',
        'body': '订单 {order_no} 已开始维修保养，预计需要 1-3 个工作日。',
        'remark': '',
    },
    'special_service_pending': {
        'title': '专项服务待确认',
        'body': '订单 {order_no} 技师发起了额外维修服务（{detail}），费用 {amount} 元，请确认。',
        'remark': '请尽快确认以免延误维修',
    },
    'ready': {
        'title': '维修已完成',
        'body': '订单 {order_no} 设备维护已全部完成，请确认是否寄回。',
        'remark': '技师将安排回寄',
    },
    'shipped': {
        'title': '设备已寄出',
        'body': '订单 {order_no} 已通过 {express} 寄出，运单号：{tracking_no}。',
        'remark': '请注意查收',
    },
    'completed': {
        'title': '订单已完成',
        'body': '订单 {order_no} 已全部完成，感谢您的信任！',
        'remark': '如有问题请联系客服',
    },
    'cancelled': {
        'title': '订单已取消',
        'body': '订单 {order_no} 已取消。',
        'remark': '如有疑问请联系客服',
    },
}

# ── 核心调度 ────────────────────────────────────────────


def _send_wechat_template(openid: str, template_id: str, data: dict,
                          url: str = '') -> bool:
    """发送微信模板消息"""
    if not WECHAT_APPID or not WECHAT_APPSECRET:
        return False
    token = _get_wechat_token()
    if not token:
        return False
    payload = {
        'touser': openid,
        'template_id': template_id,
        'data': data,
    }
    if url:
        payload['url'] = url
    try:
        r = requests.post(f'{WECHAT_MSG_URL}?access_token={token}',
                          json=payload, timeout=10)
        result = r.json()
        if result.get('errcode') == 0:
            return True
        logger.warning(f'微信模板消息发送失败: {result}')
    except Exception as e:
        logger.error(f'微信消息请求异常: {e}')
    return False


def _get_wechat_token() -> str:
    global _access_token, _access_token_expiry
    if not WECHAT_APPID or not WECHAT_APPSECRET:
        return ''
    now = datetime.now().timestamp()
    if _access_token and now < _access_token_expiry - 300:
        return _access_token
    with _lock:
        if _access_token and now < _access_token_expiry - 300:
            return _access_token
        try:
            r = requests.get(WECHAT_TOKEN_URL, params={
                'grant_type': 'client_credential',
                'appid': WECHAT_APPID,
                'secret': WECHAT_APPSECRET,
            }, timeout=10)
            result = r.json()
            if 'access_token' in result:
                _access_token = result['access_token']
                _access_token_expiry = now + result.get('expires_in', 7200)
                return _access_token
        except Exception as e:
            logger.error(f'获取微信 access_token 失败: {e}')
    return ''


def _send_sms(phone: str, content: str) -> bool:
    """发送短信（预留）"""
    if not SMS_PROVIDER or not SMS_ACCESS_KEY:
        return False
    # TODO: 接入阿里云/腾讯云短信 SDK
    logger.info(f'[SMS-{SMS_PROVIDER}] to={phone[:3]}****{phone[-4:]}: {content[:50]}')
    return False


def _send_webhook(payload: dict) -> bool:
    if not WEBHOOK_URL:
        return False
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return r.status_code < 400
    except Exception as e:
        logger.error(f'Webhook 失败: {e}')
    return False


def _dispatch(channel: str, target: str, content: dict, link_url: str = '') -> bool:
    """非阻塞投递到指定渠道，带重试"""
    for attempt in range(1 + MAX_RETRIES):
        if channel == 'wechat':
            ok = _send_wechat_template(target, content.get('template_id', ''),
                                       content.get('data', {}), link_url)
        elif channel == 'sms':
            ok = _send_sms(target, content.get('text', ''))
        elif channel == 'webhook':
            ok = _send_webhook(content)
        else:
            ok = False
        if ok:
            return True
    return False


# ── 公共 API ────────────────────────────────────────────


def notify_status_change(order_id: int, order_no: str, new_status: str,
                         customer_phone: str = '',
                         customer_wechat_openid: str = '',
                         extra: Optional[Dict[str, Any]] = None):
    """
    订单状态变更通知入口。
    后台线程执行，不阻塞请求处理。
    """
    if not NOTIFICATION_ENABLED:
        return

    tmpl = STATUS_TEMPLATES.get(new_status, {})
    if not tmpl:
        return

    # 填充模板变量
    fmt = {
        'order_no': order_no,
    }
    if extra:
        fmt.update(extra)
    body = tmpl['body'].format(**fmt)

    def _run():
        # 微信模板消息
        if customer_wechat_openid:
            wechat_data = {
                'first': {'value': tmpl['title'], 'color': '#173177'},
                'keyword1': {'value': order_no, 'color': '#173177'},
                'keyword2': {'value': body, 'color': '#173177'},
                'keyword3': {'value': datetime.now().strftime('%Y-%m-%d %H:%M'), 'color': '#173177'},
                'remark': {'value': tmpl.get('remark', ''), 'color': '#888888'},
            }
            _dispatch('wechat', customer_wechat_openid,
                      {'template_id': os.getenv('NOTIFY_WECHAT_TEMPLATE_STATUS', ''),
                       'data': wechat_data})

        # 短信
        if customer_phone:
            sms_text = f'【皓壹潜水】{tmpl["title"]}：{body}'
            _dispatch('sms', customer_phone, {'text': sms_text})

        # Webhook 保底
        _dispatch('webhook', '', {
            'event': 'order_status_change',
            'order_id': order_id,
            'order_no': order_no,
            'status': new_status,
            'title': tmpl['title'],
            'body': body,
            'timestamp': datetime.now().isoformat(),
        })

        logger.info(f'通知已发送: order={order_no}, status={new_status}')

    _executor.submit(_run)


def notify_special_service(order_id: int, order_no: str,
                           detail: str, amount: float,
                           customer_phone: str = '',
                           customer_wechat_openid: str = ''):
    """专项服务待确认通知"""
    notify_status_change(order_id, order_no, 'special_service_pending',
                         customer_phone, customer_wechat_openid,
                         {'detail': detail, 'amount': amount})


def notify_ship(order_id: int, order_no: str,
                express_company: str, tracking_no: str,
                customer_phone: str = '',
                customer_wechat_openid: str = ''):
    """快递发出通知"""
    notify_status_change(order_id, order_no, 'shipped',
                         customer_phone, customer_wechat_openid,
                         {'express': express_company, 'tracking_no': tracking_no})


def notify_cancelled(order_id: int, order_no: str,
                     customer_phone: str = '',
                     customer_wechat_openid: str = ''):
    """订单取消通知"""
    notify_status_change(order_id, order_no, 'cancelled',
                         customer_phone, customer_wechat_openid)


def _integration_hook_notify(conn, order_id: int, channel: str, status: str,
                             extra: Optional[Dict[str, Any]] = None):
    """
    内部集成钩子：给定 DB 连接 + order_id，自动查客户信息后推送。
    routes_*.py 调用此函数即可接入通知。
    """
    if not NOTIFICATION_ENABLED:
        return
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.order_no, c.phone, c.openid as wechat_openid
            FROM orders o
            LEFT JOIN customers c ON c.id = o.customer_id
            WHERE o.id = %s
        ''', (order_id,))
        row = cursor.fetchone()
        if not row:
            return
        notify_status_change(
            order_id, row['order_no'], status,
            customer_phone=row.get('phone') or '',
            customer_wechat_openid=row.get('wechat_openid') or '',
            extra=extra,
        )
    except Exception as e:
        logger.error(f'通知钩子异常: order={order_id}, {e}')
