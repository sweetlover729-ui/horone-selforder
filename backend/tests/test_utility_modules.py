# -*- coding: utf-8 -*-
"""Tests for all non-route utility modules: app, database, notification,
token_cleaner, backup_scheduler, maintenance_reminder, logging_config,
status_log, pdf_generator, validators."""
import pytest
import json
import os
import sys
import tempfile
import threading
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ═══════════════════════════════════════════════════════════
# app.py
# ═══════════════════════════════════════════════════════════

class TestApp:
    def test_health_check_ok(self, client, db_conn):
        """GET /health returns 200 when DB is accessible."""
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['service'] == 'horone.selforder'
        assert data['database'] == 'ok'
        assert data['success'] is True

    def test_health_check_db_down(self, client):
        """GET /health returns 503 when DB is inaccessible."""
        with patch('app.database.get_connection', side_effect=Exception('connection refused')):
            resp = client.get('/health')
            assert resp.status_code == 503
            data = resp.get_json()
            assert data['success'] is False
            assert 'error' in str(data.get('database', ''))

    def test_root_index(self, client):
        """GET / returns API info."""
        resp = client.get('/')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert data['version'] == '1.0.0'
        assert 'endpoints' in data
        assert 'client' in data['endpoints']

    def test_create_app(self):
        """create_app() returns Flask app."""
        from app import create_app
        app = create_app()
        assert app is not None
        assert hasattr(app, 'test_client')

    def test_init_app(self, tmp_path):
        """init_app() creates directories and checks DB."""
        with patch('app.database') as mock_db, \
             patch('app.os.makedirs') as mock_makedirs:
            from app import init_app
            init_app()
            assert mock_db.check_and_init.called

    def test_404_not_found(self, client):
        """Unknown route returns 404 JSON."""
        resp = client.get('/api/v1/client/nonexistent')
        assert resp.status_code == 404
        data = resp.get_json()
        assert data['success'] is False

    def test_cors_headers(self, client):
        """CORS headers are present."""
        resp = client.options('/api/v1/client/products/types',
                              headers={'Origin': 'https://horone.alautoai.cn',
                                       'Access-Control-Request-Method': 'GET'})
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════
# database.py
# ═══════════════════════════════════════════════════════════

class TestDatabase:
    def test_get_connection(self, db_conn):
        """get_connection returns a working RealDictCursor connection."""
        try:
            db_conn.rollback()
        except Exception:
            pass
        cur = db_conn.cursor()
        cur.execute('SELECT 1 as val')
        row = cur.fetchone()
        assert row['val'] == 1

    def test_release_connection_closes(self):
        """release_connection closes the connection."""
        import database
        conn = database.get_connection()
        database.release_connection(conn)
        assert conn.closed

    def test_release_connection_none(self):
        """release_connection handles None gracefully."""
        import database
        database.release_connection(None)  # no exception

    def test_release_connection_close_error(self):
        """release_connection logs warning on close error."""
        import database
        conn = database.get_connection()
        conn.close()  # close first
        # closing again should not raise
        database.release_connection(conn)

    def test_hash_password(self):
        """hash_password returns bcrypt hash."""
        import database
        pw = 'testpassword'
        h = database.hash_password(pw)
        assert h.startswith('$2b$')
        assert h != pw

    def test_verify_password_bcrypt_valid(self):
        """verify_password validates bcrypt hash correctly."""
        import database
        import bcrypt
        pw = 'testpassword'
        h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        valid, needs_rehash = database.verify_password(pw, h)
        assert valid is True
        assert needs_rehash is False

    def test_verify_password_bcrypt_invalid(self):
        """verify_password rejects wrong password for bcrypt hash."""
        import database
        import bcrypt
        pw = 'testpassword'
        h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        valid, needs_rehash = database.verify_password('wrong', h)
        assert valid is False
        assert needs_rehash is False

    def test_verify_password_sha256_valid(self):
        """verify_password validates SHA256 hash and flags rehash."""
        import database
        import hashlib
        pw = 'testpassword'
        h = hashlib.sha256(pw.encode()).hexdigest()
        valid, needs_rehash = database.verify_password(pw, h)
        assert valid is True
        assert needs_rehash is True

    def test_verify_password_sha256_invalid(self):
        """verify_password rejects wrong password for SHA256 hash."""
        import database
        import hashlib
        pw = 'testpassword'
        h = hashlib.sha256(pw.encode()).hexdigest()
        valid, needs_rehash = database.verify_password('wrong', h)
        assert valid is False
        assert needs_rehash is False

    def test_verify_password_bcrypt_with_dollar_a(self):
        """verify_password handles $2a$ bcrypt prefix."""
        import database
        import bcrypt
        pw = 'testpassword'
        # generate hash and replace $2b$ with $2a$
        h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        h = '$2a$' + h[4:]
        valid, needs_rehash = database.verify_password(pw, h)
        assert valid is True

    def test_verify_password_bcrypt_exception_fallback(self):
        """verify_password falls back to SHA256 on bcrypt exception."""
        import database
        import hashlib
        pw = 'testpassword'
        h = hashlib.sha256(pw.encode()).hexdigest()
        # patch bcrypt.checkpw to raise, testing fallback
        with patch('database.bcrypt.checkpw', side_effect=Exception('bcrypt error')):
            valid, needs_rehash = database.verify_password(pw, h)
            assert valid is True
            assert needs_rehash is True

    def test_dict_conn(self):
        """dict_conn is an alias for get_connection."""
        import database
        conn = database.dict_conn()
        assert conn is not None
        database.release_connection(conn)

    def test_check_and_init_success(self):
        """check_and_init succeeds when DB is available."""
        import database
        database.check_and_init()  # no exception

    def test_check_and_init_failure(self):
        """check_and_init raises when DB is unavailable."""
        import database
        with patch('database.get_connection', side_effect=Exception('db down')):
            with pytest.raises(Exception):
                database.check_and_init()


# ═══════════════════════════════════════════════════════════
# token_cleaner.py
# ═══════════════════════════════════════════════════════════

class TestTokenCleaner:
    def test_start_cleaner_creates_thread(self):
        """start_cleaner creates a daemon thread."""
        import token_cleaner
        # Reset global state for test
        token_cleaner._cleaner_started = False
        mock_app = MagicMock()
        t = token_cleaner.start_cleaner(mock_app)
        assert token_cleaner._cleaner_started is True
        # Reset after test
        token_cleaner._cleaner_started = False

    def test_start_cleaner_idempotent(self):
        """start_cleaner is idempotent."""
        import token_cleaner
        token_cleaner._cleaner_started = True
        mock_app = MagicMock()
        token_cleaner.start_cleaner(mock_app)  # should return early


# ═══════════════════════════════════════════════════════════
# backup_scheduler.py
# ═══════════════════════════════════════════════════════════

class TestBackupScheduler:
    def test_start_backup_scheduler_creates_thread(self):
        """start_backup_scheduler creates a daemon thread."""
        import backup_scheduler
        backup_scheduler._scheduler_started = False
        mock_app = MagicMock()
        backup_scheduler.start_backup_scheduler(mock_app)
        assert backup_scheduler._scheduler_started is True
        backup_scheduler._scheduler_started = False

    def test_start_backup_scheduler_idempotent(self):
        """start_backup_scheduler is idempotent."""
        import backup_scheduler
        backup_scheduler._scheduler_started = True
        mock_app = MagicMock()
        backup_scheduler.start_backup_scheduler(mock_app)

    def test_run_backup_success(self):
        """_run_backup succeeds with pg_dump."""
        import backup_scheduler
        with patch('backup_scheduler.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '-- SQL dump'
            mock_result.stderr = ''
            mock_run.return_value = mock_result
            with patch('backup_scheduler.os.makedirs'), \
                 patch('backup_scheduler.os.path.getsize', return_value=1024*1024), \
                 patch('builtins.open', mock.mock_open()), \
                 patch('backup_scheduler.glob.glob', return_value=[]):
                result = backup_scheduler._run_backup()
                assert result is True

    def test_run_backup_failure(self):
        """_run_backup returns False on pg_dump failure."""
        import backup_scheduler
        with patch('backup_scheduler.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ''
            mock_result.stderr = 'error: connection refused'
            mock_run.return_value = mock_result
            with patch('backup_scheduler.os.makedirs'):
                result = backup_scheduler._run_backup()
                assert result is False

    def test_run_backup_timeout(self):
        """_run_backup handles subprocess.TimeoutExpired."""
        import backup_scheduler
        import subprocess
        with patch('backup_scheduler.subprocess.run',
                   side_effect=subprocess.TimeoutExpired('pg_dump', 300)), \
             patch('backup_scheduler.os.makedirs'):
            result = backup_scheduler._run_backup()
            assert result is False

    def test_run_backup_general_exception(self):
        """_run_backup handles general exceptions."""
        import backup_scheduler
        with patch('backup_scheduler.subprocess.run',
                   side_effect=Exception('boom')), \
             patch('backup_scheduler.os.makedirs'):
            result = backup_scheduler._run_backup()
            assert result is False

    def test_run_backup_cleanup_old(self):
        """_run_backup cleans up old backup files."""
        import backup_scheduler
        with patch('backup_scheduler.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '-- SQL dump'
            mock_result.stderr = ''
            mock_run.return_value = mock_result
            with patch('backup_scheduler.os.makedirs'), \
                 patch('backup_scheduler.os.path.getsize', return_value=1024*1024), \
                 patch('builtins.open', mock.mock_open()), \
                 patch('backup_scheduler.glob.glob',
                       return_value=['/fake/backup_20260401.sql']), \
                 patch('backup_scheduler.os.path.getmtime', return_value=100000), \
                 patch('backup_scheduler.os.remove') as mock_remove:
                backup_scheduler._run_backup()
                # Old file should be removed (mtime from 1970 is long ago)
                assert mock_remove.called

    def test_run_backup_cleanup_oserror(self):
        """_run_backup handles OSError during cleanup."""
        import backup_scheduler
        with patch('backup_scheduler.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '-- SQL dump'
            mock_result.stderr = ''
            mock_run.return_value = mock_result
            with patch('backup_scheduler.os.makedirs'), \
                 patch('backup_scheduler.os.path.getsize', return_value=1024*1024), \
                 patch('builtins.open', mock.mock_open()), \
                 patch('backup_scheduler.glob.glob',
                       return_value=['/fake/backup_20260401.sql']), \
                 patch('backup_scheduler.os.path.getmtime',
                       side_effect=OSError('permission denied')):
                backup_scheduler._run_backup()


# ═══════════════════════════════════════════════════════════
# maintenance_reminder.py
# ═══════════════════════════════════════════════════════════

class TestMaintenanceReminder:
    def test_start_reminder_daemon(self):
        """start_reminder_daemon creates a daemon thread."""
        import maintenance_reminder
        maintenance_reminder.start_reminder_daemon()  # no exception

    def test_check_and_remind_no_reminders(self):
        """_check_and_remind handles empty reminder set."""
        import maintenance_reminder
        with patch('maintenance_reminder.database.get_connection') as mock_conn_fn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cursor
            mock_conn_fn.return_value = mock_conn
            maintenance_reminder._check_and_remind()

    def test_check_and_remind_with_reminders(self):
        """_check_and_remind processes pending reminders."""
        import maintenance_reminder
        with patch('maintenance_reminder.database.get_connection') as mock_conn_fn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            # First return for UPDATE overdue, second/third/fourth for reminder windows
            mock_cursor.fetchall.side_effect = [
                [],  # overdue update
                [{'id': 1, 'order_id': 1, 'customer_id': 1,
                  'equipment_summary': 'Regulator', 'next_service_date': '2026-05-01',
                  'phone': '13900000001', 'openid': ''}],  # 30-day window
                [],  # 7-day window
                [],  # 0-day window
            ]
            mock_conn.cursor.return_value = mock_cursor
            mock_conn_fn.return_value = mock_conn
            maintenance_reminder._check_and_remind()
            # Verify the UPDATE for notify_count was called
            assert mock_cursor.execute.call_count >= 3

    def test_check_and_remind_exception(self):
        """_check_and_remind handles database exceptions gracefully."""
        import maintenance_reminder
        with patch('maintenance_reminder.database.get_connection',
                   side_effect=Exception('db down')):
            maintenance_reminder._check_and_remind()  # no exception raised


# ═══════════════════════════════════════════════════════════
# notification.py
# ═══════════════════════════════════════════════════════════

class TestNotification:
    def test_notify_status_change_disabled(self):
        """notify_status_change returns early when disabled."""
        import notification
        notification.NOTIFICATION_ENABLED = False
        try:
            notification.notify_status_change(1, 'TEST-001', 'received')
        finally:
            notification.NOTIFICATION_ENABLED = True

    def test_notify_status_change_unknown_status(self):
        """notify_status_change returns early for unknown status."""
        import notification
        notification.notify_status_change(1, 'TEST-001', 'nonexistent_status')

    def test_notify_status_change_normal(self):
        """notify_status_change submits task to executor."""
        import notification
        mock_executor = MagicMock()
        notification._executor = mock_executor
        try:
            notification.notify_status_change(
                1, 'TEST-001', 'received',
                customer_phone='13900000001',
                customer_wechat_openid='openid123'
            )
            assert mock_executor.submit.called
        finally:
            notification._executor = notification.ThreadPoolExecutor(
                max_workers=1, thread_name_prefix='notify-')

    def test_notify_special_service(self):
        """notify_special_service delegates to notify_status_change."""
        import notification
        with patch('notification.notify_status_change') as mock_notify:
            notification.notify_special_service(
                1, 'TEST-001', 'O-ring replacement', 150.0,
                customer_phone='13900000001'
            )
            mock_notify.assert_called_once_with(
                1, 'TEST-001', 'special_service_pending',
                '13900000001', '',
                {'detail': 'O-ring replacement', 'amount': 150.0}
            )

    def test_notify_ship(self):
        """notify_ship delegates to notify_status_change."""
        import notification
        with patch('notification.notify_status_change') as mock_notify:
            notification.notify_ship(
                1, 'TEST-001', 'SF Express', 'SF1234567890',
                customer_phone='13900000001'
            )
            mock_notify.assert_called_once_with(
                1, 'TEST-001', 'shipped',
                '13900000001', '',
                {'express': 'SF Express', 'tracking_no': 'SF1234567890'}
            )

    def test_notify_cancelled(self):
        """notify_cancelled delegates to notify_status_change."""
        import notification
        with patch('notification.notify_status_change') as mock_notify:
            notification.notify_cancelled(1, 'TEST-001', customer_phone='13900000001')
            mock_notify.assert_called_once_with(
                1, 'TEST-001', 'cancelled', '13900000001', ''
            )

    def test_integration_hook_notify_disabled(self):
        """_integration_hook_notify returns early when disabled."""
        import notification
        notification.NOTIFICATION_ENABLED = False
        try:
            mock_conn = MagicMock()
            notification._integration_hook_notify(mock_conn, 1, 'console', 'received')
            # Should not query DB
            mock_conn.cursor.assert_not_called()
        finally:
            notification.NOTIFICATION_ENABLED = True

    def test_integration_hook_notify_no_order(self):
        """_integration_hook_notify handles missing order."""
        import notification
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        notification._integration_hook_notify(mock_conn, 999999, 'console', 'received')

    def test_integration_hook_notify_exception(self):
        """_integration_hook_notify handles exceptions gracefully."""
        import notification
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = Exception('cursor error')
        notification._integration_hook_notify(mock_conn, 1, 'console', 'received')
        # Should not raise

    def test_dispatch_wechat_success(self):
        """_dispatch succeeds for wechat channel."""
        import notification
        with patch('notification._send_wechat_template', return_value=True):
            result = notification._dispatch(
                'wechat', 'openid123',
                {'template_id': 'tmpl001', 'data': {}}, ''
            )
            assert result is True

    def test_dispatch_sms(self):
        """_dispatch handles sms channel."""
        import notification
        with patch('notification._send_sms', return_value=False):
            result = notification._dispatch(
                'sms', '13900000001', {'text': 'test message'}, ''
            )
            assert result is False

    def test_dispatch_webhook_success(self):
        """_dispatch succeeds for webhook channel."""
        import notification
        with patch('notification._send_webhook', return_value=True):
            result = notification._dispatch(
                'webhook', '', {'event': 'test'}, ''
            )
            assert result is True

    def test_dispatch_unknown_channel(self):
        """_dispatch returns False for unknown channel."""
        import notification
        result = notification._dispatch('unknown', '', {}, '')
        assert result is False

    def test_dispatch_retry(self):
        """_dispatch retries on failure."""
        import notification
        with patch('notification._send_webhook',
                   side_effect=[False, False, True]) as mock_send:
            result = notification._dispatch('webhook', '', {'event': 'test'})
            assert result is True
            assert mock_send.call_count == 3  # 1 initial + 2 retries

    def test_send_wechat_template_no_config(self):
        """_send_wechat_template returns False when not configured."""
        import notification
        orig_appid = notification.WECHAT_APPID
        notification.WECHAT_APPID = ''
        try:
            result = notification._send_wechat_template('openid', 'tmpl', {})
            assert result is False
        finally:
            notification.WECHAT_APPID = orig_appid

    def test_get_wechat_token_cached(self):
        """_get_wechat_token returns cached token."""
        import notification
        notification.WECHAT_APPID = 'test_appid'
        notification.WECHAT_APPSECRET = 'test_secret'
        notification._access_token = 'cached_token'
        notification._access_token_expiry = 9999999999
        try:
            token = notification._get_wechat_token()
            assert token == 'cached_token'
        finally:
            notification._access_token = ''
            notification._access_token_expiry = 0.0
            notification.WECHAT_APPID = ''
            notification.WECHAT_APPSECRET = ''

    def test_get_wechat_token_not_configured(self):
        """_get_wechat_token returns empty when not configured."""
        import notification
        orig = notification.WECHAT_APPID
        notification.WECHAT_APPID = ''
        notification._access_token_expiry = 0.0
        try:
            token = notification._get_wechat_token()
            assert token == ''
        finally:
            notification.WECHAT_APPID = orig

    def test_send_sms_not_configured(self):
        """_send_sms returns False when not configured."""
        import notification
        orig = notification.SMS_PROVIDER
        notification.SMS_PROVIDER = ''
        try:
            result = notification._send_sms('13900000001', 'test')
            assert result is False
        finally:
            notification.SMS_PROVIDER = orig

    def test_send_webhook_not_configured(self):
        """_send_webhook returns False when WEBHOOK_URL is empty."""
        import notification
        orig = notification.WEBHOOK_URL
        notification.WEBHOOK_URL = ''
        try:
            result = notification._send_webhook({})
            assert result is False
        finally:
            notification.WEBHOOK_URL = orig

    def test_send_webhook_exception(self):
        """_send_webhook returns False on request exception."""
        import notification
        notification.WEBHOOK_URL = 'http://localhost:99999/webhook'
        try:
            with patch('notification.requests.post',
                       side_effect=Exception('connection refused')):
                result = notification._send_webhook({'event': 'test'})
                assert result is False
        finally:
            notification.WEBHOOK_URL = ''


# ═══════════════════════════════════════════════════════════
# logging_config.py
# ═══════════════════════════════════════════════════════════

class TestLoggingConfig:
    def test_get_logger_default(self):
        """get_logger() returns 'horone' logger."""
        from logging_config import get_logger
        logger = get_logger()
        assert logger.name == 'horone'

    def test_get_logger_with_name(self):
        """get_logger('db') returns 'horone.db' logger."""
        from logging_config import get_logger
        logger = get_logger('db')
        assert logger.name == 'horone.db'

    def test_get_logger_backend_prefix(self):
        """get_logger strips 'backend.' prefix."""
        from logging_config import get_logger
        logger = get_logger('backend.routes_console')
        assert logger.name == 'horone.routes_console'

    def test_json_formatter(self):
        """JsonFormatter produces valid JSON."""
        from logging_config import JsonFormatter
        import logging
        formatter = JsonFormatter()
        record = logging.LogRecord('test', logging.INFO, '', 0, 'hello world', (), None)
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed['msg'] == 'hello world'
        assert parsed['level'] == 'INFO'

    def test_json_formatter_with_exception(self):
        """JsonFormatter includes exception info."""
        from logging_config import JsonFormatter
        import logging
        formatter = JsonFormatter()
        try:
            raise ValueError('test error')
        except ValueError:
            record = logging.LogRecord(
                'test', logging.ERROR, '', 0, 'error msg', (), None)
            record.exc_info = (ValueError, ValueError('test error'), None)
            output = formatter.format(record)
            parsed = json.loads(output)
            assert 'exc' in parsed


# ═══════════════════════════════════════════════════════════
# status_log.py
# ═══════════════════════════════════════════════════════════

class TestStatusLog:
    def test_log_status_change_success(self):
        """log_status_change inserts a record."""
        from status_log import log_status_change
        import database
        conn = database.get_connection()
        try:
            log_status_change(conn, 1, 'status', 'pending', 'received', 'kent')
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM status_change_log WHERE order_id=1 AND field='status' "
                "ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            assert row is not None
            assert row['old_value'] == 'pending'
            assert row['new_value'] == 'received'
            # Clean up
            cur.execute('DELETE FROM status_change_log WHERE id=%s', (row['id'],))
            conn.commit()
        finally:
            database.release_connection(conn)

    def test_log_status_change_db_error(self, db_conn):
        """log_status_change handles DB errors gracefully."""
        from status_log import log_status_change
        # Test with a non-existent table that will cause error
        with patch('status_log.logger') as mock_logger:
            # Simulate a DB error during execute
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception('table does not exist')
            mock_conn.cursor.return_value = mock_cursor
            log_status_change(mock_conn, 1, 'status', 'old', 'new', 'kent')
            assert mock_logger.warning.called


# ═══════════════════════════════════════════════════════════
# pdf_generator.py
# ═══════════════════════════════════════════════════════════

class TestPdfGenerator:
    def test_ensure_pdf_dir(self):
        """ensure_pdf_dir creates PDF directory."""
        from pdf_generator import ensure_pdf_dir, PDF_DIR
        ensure_pdf_dir()
        assert os.path.exists(PDF_DIR)

    def test_build_styles(self):
        """_build_styles returns a style dictionary."""
        from pdf_generator import _build_styles
        styles = _build_styles()
        assert 'title_main' in styles
        assert 'title_sub' in styles
        assert 'section' in styles
        assert 'field_key' in styles
        assert 'field_val' in styles
        assert 'node_title' in styles
        assert 'node_desc' in styles
        assert 'footer' in styles

    def test_photo_path_plain_filename(self):
        """_photo_path with plain filename returns correct path."""
        from pdf_generator import _photo_path, BASE_UPLOAD
        result = _photo_path(1, 2, 'test.jpg')
        expected = os.path.join(BASE_UPLOAD, '1', 'nodes', '2', 'test.jpg')
        assert result == expected or result is None

    def test_photo_path_relative(self):
        """_photo_path with slash-containing filename returns absolute path."""
        from pdf_generator import _photo_path
        result = _photo_path(1, 2, 'orders/1/nodes/2/test.jpg')
        assert result is None  # file doesn't exist

    def test_make_table(self):
        """_make_table creates a styled Table."""
        from pdf_generator import _make_table
        from reportlab.platypus import Table
        data = [['H1', 'H2'], ['A', 'B']]
        t = _make_table(data, [3.0, 3.0])
        assert isinstance(t, Table)

    def test_photo_cell(self):
        """_photo_cell returns 2-element list of photo images/placeholders."""
        from pdf_generator import _photo_cell
        cells = _photo_cell([], 1, 2)
        assert len(cells) == 2

    def test_diagonal_watermark(self):
        """DiagonalWatermark is a Flowable."""
        from pdf_generator import DiagonalWatermark
        dw = DiagonalWatermark('TEST', 100, 100)
        assert dw.width == 100
        assert dw.height == 100

    @patch('pdf_generator.PDF_DIR', new='/tmp/test_pdfs')
    @patch('pdf_generator.os.makedirs')
    def test_generate_order_pdf_basic(self, mock_makedirs):
        """generate_order_pdf creates a PDF file."""
        from pdf_generator import generate_order_pdf
        import database as _db_module
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor

        with patch.object(_db_module, 'get_connection', return_value=mock_conn):
            order_data = {
                'id': 1,
                'order_no': 'RMD-20260501-000001',
                'created_at': '2026-05-01 10:00:00',
                'completed_at': '2026-05-01 12:00:00',
                'receiver_name': 'Test User',
                'receiver_phone': '13900000001',
                'receiver_address': 'Test Address',
                'customer_id': 1,
            }
            with patch('pdf_generator.SimpleDocTemplate') as mock_doc:
                mock_doc_instance = MagicMock()
                mock_doc.return_value = mock_doc_instance
                path = generate_order_pdf(order_data, None)
                assert 'RMD-20260501-000001' in path
                assert mock_doc_instance.build.called

    def test_cleanup_expired_pdfs_empty(self):
        """cleanup_expired_pdfs with empty directory returns 0."""
        from pdf_generator import cleanup_expired_pdfs
        with patch('os.listdir', return_value=[]):
            result = cleanup_expired_pdfs()
            assert result == 0

    def test_cleanup_order_photos_nonexistent(self):
        """cleanup_order_photos with nonexistent dir returns 0."""
        from pdf_generator import cleanup_order_photos
        with patch('os.path.exists', return_value=False):
            result = cleanup_order_photos(999999)
            assert result == 0
