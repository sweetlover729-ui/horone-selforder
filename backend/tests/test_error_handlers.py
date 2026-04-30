"""Tests for error_handlers module"""
import pytest
from flask import jsonify
from error_handlers import (
    APIError, handle_api_error, handle_generic_error,
    handle_not_found, handle_method_not_allowed, handle_bad_request,
    log_request_info, log_response_info, ERROR_CODES, get_error_message
)


class TestAPIError:
    def test_default_status_code(self):
        e = APIError('test error')
        assert e.message == 'test error'
        assert e.status_code == 400
        assert e.error_code == 'ERR_400'
    def test_custom_status_code(self):
        e = APIError('forbidden', status_code=403, error_code='CUSTOM')
        assert e.status_code == 403
        assert e.error_code == 'CUSTOM'
    def test_auto_error_code(self):
        e = APIError('not found', status_code=404)
        assert e.error_code == 'ERR_404'


class TestHandleApiError:
    def test_returns_correct_structure(self, client):
        with client.application.test_request_context():
            e = APIError('bad request', status_code=400, error_code='ERR_BAD')
            resp, status = handle_api_error(e)
            data = resp.get_json()
            assert data['success'] is False
            assert status == 400


class TestHandleGenericError:
    def test_returns_500(self, client):
        with client.application.test_request_context():
            e = ValueError('something broke')
            resp, status = handle_generic_error(e)
            data = resp.get_json()
            assert data['success'] is False
            assert status == 500

    def test_includes_detail_in_dev_mode(self, client, monkeypatch):
        monkeypatch.setenv('FLASK_ENV', 'development')
        with client.application.test_request_context():
            e = ValueError('dev error')
            resp, status = handle_generic_error(e)
            data = resp.get_json()
            assert 'detail' in data
            assert 'traceback' in data


class TestHandleNotFound:
    def test_returns_404(self, client):
        with client.application.test_request_context():
            resp, status = handle_not_found(None)
            assert status == 404


class TestHandleMethodNotAllowed:
    def test_returns_405(self, client):
        with client.application.test_request_context():
            resp, status = handle_method_not_allowed(None)
            assert status == 405


class TestHandleBadRequest:
    def test_returns_400(self, client):
        with client.application.test_request_context():
            resp, status = handle_bad_request(None)
            assert status == 400


class TestLogRequestInfo:
    def test_does_not_crash(self, client):
        with client.application.test_request_context('/', method='GET', environ_base={'REMOTE_ADDR': '127.0.0.1'}):
            log_request_info()


class TestLogResponseInfo:
    def test_logs_response(self, client):
        with client.application.test_request_context('/'):
            resp = client.application.response_class(status=200)
            result = log_response_info(resp)
            assert result is resp


class TestGetErrorMessage:
    def test_known_code(self):
        assert get_error_message('ERR_400') == '请求参数错误'
        assert get_error_message('ERR_404') == '资源不存在'
    def test_unknown_code(self):
        assert get_error_message('NONEXISTENT') == '未知错误'


class TestErrorCodes:
    def test_has_standard_codes(self):
        assert 'ERR_400' in ERROR_CODES
        assert 'ERR_401' in ERROR_CODES
        assert 'ERR_403' in ERROR_CODES
        assert 'ERR_500' in ERROR_CODES
