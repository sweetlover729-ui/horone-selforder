# -*- coding: utf-8 -*-
"""notification.py 专项测试 — 补齐未覆盖路径"""
import pytest
import notification
from unittest.mock import patch, MagicMock
from datetime import datetime
import os


class TestNotificationGap:
    """补齐: lines 98-117, 127-143, 151-152, 160, 212-219"""

    # ── _send_wechat_template (98-117) ──

    def test_send_wechat_template_success(self, monkeypatch):
        """完整成功路径 → 覆盖 98-113"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_test123')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'sec_test456')

        with patch.object(notification, '_get_wechat_token', return_value='mock_token_abc'):
            with patch('notification.requests.post') as mock_post:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {'errcode': 0}
                mock_post.return_value = mock_resp

                result = notification._send_wechat_template(
                    'openid_123', 'tmpl_1', {'key': 'val'}, url='https://link')

                assert result is True
                call_args = mock_post.call_args
                assert 'mock_token_abc' in call_args[0][0]

    def test_send_wechat_template_post_failure(self, monkeypatch):
        """微信返回非零 errcode → 覆盖 114"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_test123')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'sec_test456')

        with patch.object(notification, '_get_wechat_token', return_value='mock_token_abc'):
            with patch('notification.requests.post') as mock_post:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {'errcode': 40001}
                mock_post.return_value = mock_resp

                result = notification._send_wechat_template('openid_123', 'tmpl_1', {}, '')
                assert result is False

    def test_send_wechat_template_exception(self, monkeypatch):
        """请求异常 → 覆盖 115-116"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_test123')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'sec_test456')

        with patch.object(notification, '_get_wechat_token', return_value='mock_token_abc'):
            with patch('notification.requests.post', side_effect=Exception('network error')):
                result = notification._send_wechat_template('openid_123', 'tmpl_1', {}, '')
                assert result is False

    def test_send_wechat_template_no_token(self, monkeypatch):
        """token 获取失败 → 覆盖 99-100"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_test123')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'sec_test456')

        with patch.object(notification, '_get_wechat_token', return_value=''):
            result = notification._send_wechat_template('openid_123', 'tmpl_1', {}, '')
            assert result is False

    # ── _get_wechat_token (127-143) ──

    def test_get_wechat_token_fresh_refresh(self, monkeypatch):
        """首次获取 token → 覆盖 127-140"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_test123')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'sec_test456')
        monkeypatch.setattr(notification, '_access_token', '')
        monkeypatch.setattr(notification, '_access_token_expiry', 0.0)

        with patch('notification.requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {'access_token': 'fresh_xyz', 'expires_in': 7200}
            mock_get.return_value = mock_resp

            token = notification._get_wechat_token()
            assert token == 'fresh_xyz'
            assert notification._access_token == 'fresh_xyz'
            assert notification._access_token_expiry > datetime.now().timestamp()

    def test_get_wechat_token_exception(self, monkeypatch):
        """请求异常 → 覆盖 141-143"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_test123')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'sec_test456')
        monkeypatch.setattr(notification, '_access_token', '')
        monkeypatch.setattr(notification, '_access_token_expiry', 0.0)

        with patch('notification.requests.get', side_effect=Exception('timeout')):
            token = notification._get_wechat_token()
            assert token == ''

    # ── _send_sms (151-152) ──

    def test_send_sms_configured(self, monkeypatch):
        """配置了 SMS provider 和 key → 覆盖 151-152"""
        monkeypatch.setattr(notification, 'SMS_PROVIDER', 'aliyun')
        monkeypatch.setattr(notification, 'SMS_ACCESS_KEY', 'ak_test')
        result = notification._send_sms('13912345678', '测试短信内容')
        assert result is False  # TODO placeholder, still returns False

    # ── _send_webhook (160) ──

    def test_send_webhook_success(self, monkeypatch):
        """webhook 成功 → 覆盖 160"""
        monkeypatch.setattr(notification, 'WEBHOOK_URL', 'https://webhook.test/hook')

        with patch('notification.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            result = notification._send_webhook({'event': 'test', 'data': 'hello'})
            assert result is True

    def test_send_webhook_exception(self, monkeypatch):
        """webhook 异常 → 覆盖 161-162"""
        monkeypatch.setattr(notification, 'WEBHOOK_URL', 'https://webhook.test/hook')

        with patch('notification.requests.post', side_effect=Exception('connection refused')):
            result = notification._send_webhook({'event': 'test'})
            assert result is False

    def test_send_webhook_failure_status(self, monkeypatch):
        """webhook 返回 500 → 覆盖 160 else branch"""
        monkeypatch.setattr(notification, 'WEBHOOK_URL', 'https://webhook.test/hook')

        with patch('notification.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_post.return_value = mock_resp

            result = notification._send_webhook({'event': 'test'})
            assert result is False

    # ── _dispatch (retry, channel routing) ──

    def test_dispatch_retry_success(self, monkeypatch):
        """首次失败，第二次成功 → 覆盖 178-179 重试"""
        monkeypatch.setattr(notification, 'MAX_RETRIES', 2)
        call_count = [0]

        def mock_webhook(payload):
            call_count[0] += 1
            return call_count[0] >= 2

        with patch.object(notification, '_send_webhook', side_effect=mock_webhook):
            result = notification._dispatch('webhook', '', {'event': 'retry_test'})
            assert result is True
            assert call_count[0] == 2

    def test_dispatch_all_fail(self, monkeypatch):
        """所有重试失败 → 覆盖 180"""
        monkeypatch.setattr(notification, 'MAX_RETRIES', 1)
        with patch.object(notification, '_send_webhook', return_value=False):
            result = notification._dispatch('webhook', '', {'event': 'fail'})
            assert result is False

    # ── notify_status_change._run() (212-219) ──

    def test_notify_run_with_wechat(self, monkeypatch):
        """notify_status_change 内 _run 封面 212-219 wechat + 239 log"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        monkeypatch.setattr(notification, 'MAX_RETRIES', 1)

        captured_fn = []

        class FakeExecutor:
            def submit(self, fn):
                captured_fn.append(fn)

        monkeypatch.setattr(notification, '_executor', FakeExecutor())

        with patch.object(notification, '_dispatch') as mock_dispatch:
            notification.notify_status_change(
                1, 'RMD-2026-001', 'received',
                customer_wechat_openid='openid_test_123',
                customer_phone='13900000001')

            assert len(captured_fn) == 1
            captured_fn[0]()  # execute synchronously

            # 3 dispatches: wechat + sms + webhook
            assert mock_dispatch.call_count == 3
            calls = [c[0] for c in mock_dispatch.call_args_list]
            channels = [c[0] for c in calls]
            assert 'wechat' in channels
            assert 'sms' in channels
            assert 'webhook' in channels

    def test_notify_disabled(self, monkeypatch):
        """通知已禁用 → 194-195"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', False)
        # Should not raise, should just return
        notification.notify_status_change(1, 'RMD-001', 'received',
                                          customer_wechat_openid='openid_123')

    def test_notify_unknown_status(self, monkeypatch):
        """未知状态 → 198-199"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        # 'unknown_status' not in STATUS_TEMPLATES
        notification.notify_status_change(1, 'RMD-001', 'unknown_status')

    def test_notify_with_extra_formatting(self, monkeypatch):
        """带 extra 参数的格式填充 → 覆盖 205-206"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        captured_fn = []

        class FakeExecutor:
            def submit(self, fn):
                captured_fn.append(fn)

        monkeypatch.setattr(notification, '_executor', FakeExecutor())

        with patch.object(notification, '_dispatch'):
            notification.notify_status_change(
                2, 'RMD-002', 'shipped',
                customer_phone='13900000002',
                extra={'express': '顺丰', 'tracking_no': 'SF1234567890'})

            assert len(captured_fn) == 1

    # ── Integration hook (272-298) ──

    def test_integration_hook_success(self, monkeypatch, db_conn):
        """_integration_hook_notify 成功路径"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        captured_fn = []

        class FakeExecutor:
            def submit(self, fn):
                captured_fn.append(fn)

        monkeypatch.setattr(notification, '_executor', FakeExecutor())

        notification._integration_hook_notify(db_conn, 1, 'wechat', 'received')
        # Should submit a task if order exists

    def test_integration_hook_disabled(self, monkeypatch, db_conn):
        """通知禁用时不执行"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', False)
        notification._integration_hook_notify(db_conn, 1, 'wechat', 'received')

    def test_integration_hook_order_not_found(self, monkeypatch, db_conn):
        """订单不存在 → 289-290"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        notification._integration_hook_notify(db_conn, 99999, 'wechat', 'received')
class TestNotificationFinalGap:
    """补齐剩余 14 missed: 97,123,126,129,149,157,170,173,177,249,259,268,297-298"""

    # ── 守卫返回路径 ──

    def test_send_wechat_template_not_configured(self, monkeypatch):
        """WECHAT_APPID 为空 → 96-97"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', '')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', '')
        result = notification._send_wechat_template('openid', 'tmpl', {})
        assert result is False

    def test_get_wechat_token_not_configured(self, monkeypatch):
        """WECHAT_APPID 为空 → 122-123"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', '')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', '')
        token = notification._get_wechat_token()
        assert token == ''

    def test_get_wechat_token_cached(self, monkeypatch):
        """缓存 token 未过期 → 125-126"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_app')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'wx_sec')
        monkeypatch.setattr(notification, '_access_token', 'cached_tk')
        monkeypatch.setattr(notification, '_access_token_expiry',
                            datetime.now().timestamp() + 3600)
        token = notification._get_wechat_token()
        assert token == 'cached_tk'

    def test_get_wechat_token_double_check(self, monkeypatch):
        """进入锁后发现另一线程已刷新 → 128-129"""
        monkeypatch.setattr(notification, 'WECHAT_APPID', 'wx_app')
        monkeypatch.setattr(notification, 'WECHAT_APPSECRET', 'wx_sec')
        monkeypatch.setattr(notification, '_access_token', '')
        monkeypatch.setattr(notification, '_access_token_expiry', 0.0)

        class FakeLock:
            def __enter__(self):
                # 模拟另一线程已刷新
                notification._access_token = 'double_checked'
                notification._access_token_expiry = datetime.now().timestamp() + 7200
                return None
            def __exit__(self, *args):
                pass

        monkeypatch.setattr(notification, '_lock', FakeLock())
        with patch('notification.requests.get') as mock_get:
            token = notification._get_wechat_token()
            assert token == 'double_checked'
            mock_get.assert_not_called()

    def test_send_sms_not_configured(self, monkeypatch):
        """SMS 未配置 → 148-149"""
        monkeypatch.setattr(notification, 'SMS_PROVIDER', '')
        monkeypatch.setattr(notification, 'SMS_ACCESS_KEY', '')
        result = notification._send_sms('13900000001', 'test')
        assert result is False

    def test_send_webhook_not_configured(self, monkeypatch):
        """WEBHOOK_URL 为空 → 156-157"""
        monkeypatch.setattr(notification, 'WEBHOOK_URL', '')
        result = notification._send_webhook({'event': 'test'})
        assert result is False

    # ── _dispatch 各渠道 ──

    def test_dispatch_wechat_channel(self, monkeypatch):
        """_dispatch wechat 渠道 → 169-171"""
        monkeypatch.setattr(notification, 'MAX_RETRIES', 1)
        with patch.object(notification, '_send_wechat_template', return_value=True):
            result = notification._dispatch(
                'wechat', 'openid_abc',
                {'template_id': 'tmpl_x', 'data': {'k': 'v'}}, 'https://link')
            assert result is True

    def test_dispatch_sms_channel(self, monkeypatch):
        """_dispatch sms 渠道 → 172-173"""
        monkeypatch.setattr(notification, 'MAX_RETRIES', 1)
        with patch.object(notification, '_send_sms', return_value=True):
            result = notification._dispatch(
                'sms', '13900000001', {'text': 'hello'})
            assert result is True

    def test_dispatch_unknown_channel(self, monkeypatch):
        """_dispatch 未知渠道 → 176-177"""
        monkeypatch.setattr(notification, 'MAX_RETRIES', 1)
        result = notification._dispatch('unknown', 'target', {})
        assert result is False

    # ── 公共包装函数 ──

    def test_notify_special_service_wrapper(self, monkeypatch):
        """notify_special_service → 245-251"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        captured_fn = []

        class FakeExecutor:
            def submit(self, fn):
                captured_fn.append(fn)

        monkeypatch.setattr(notification, '_executor', FakeExecutor())

        notification.notify_special_service(1, 'RMD-001', '更换O圈', 150.0,
                                            customer_wechat_openid='oid_1')
        assert len(captured_fn) == 1

    def test_notify_ship_wrapper(self, monkeypatch):
        """notify_ship → 255-261"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        captured_fn = []

        class FakeExecutor:
            def submit(self, fn):
                captured_fn.append(fn)

        monkeypatch.setattr(notification, '_executor', FakeExecutor())

        notification.notify_ship(1, 'RMD-001', '顺丰', 'SF123',
                                 customer_phone='13900000001')
        assert len(captured_fn) == 1

    def test_notify_cancelled_wrapper(self, monkeypatch):
        """notify_cancelled → 265-269"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        captured_fn = []

        class FakeExecutor:
            def submit(self, fn):
                captured_fn.append(fn)

        monkeypatch.setattr(notification, '_executor', FakeExecutor())

        notification.notify_cancelled(1, 'RMD-001',
                                      customer_phone='13900000001')
        assert len(captured_fn) == 1

    # ── _integration_hook_notify 异常分支 ──

    def test_integration_hook_exception(self, monkeypatch):
        """integration hook 异常 → 297-298"""
        monkeypatch.setattr(notification, 'NOTIFICATION_ENABLED', True)
        from unittest.mock import MagicMock
        bad_conn = MagicMock()
        bad_conn.cursor.side_effect = Exception('simulated DB error')
        # 不应抛出异常
        notification._integration_hook_notify(bad_conn, 1, 'wechat', 'received')
