"""Tests for auth module"""
import pytest
from auth import generate_token, validate_staff_token, validate_customer_token, require_admin, admin_required
from flask import jsonify


class TestGenerateToken:
    def test_token_length(self):
        t = generate_token()
        assert len(t) == 32
    def test_token_hex(self):
        t = generate_token()
        int(t, 16)
    def test_two_tokens_different(self):
        assert generate_token() != generate_token()


class TestValidateStaffToken:
    def test_none_token(self):
        assert validate_staff_token(None) is None
    def test_empty_token(self):
        assert validate_staff_token('') is None
    def test_invalid_token(self):
        assert validate_staff_token('invalid_token_xxxxxxxxxxxx') is None
    def test_valid_staff_token(self, client, staff_token):
        result = validate_staff_token(staff_token)
        assert result is not None
        assert result['username'] == 'kent'
    def test_allow_inactive_param(self, client, staff_token):
        result = validate_staff_token(staff_token, allow_inactive=True)
        assert result is not None


class TestValidateCustomerToken:
    def test_none_token(self):
        assert validate_customer_token(None) is None
    def test_empty_token(self):
        assert validate_customer_token('') is None


class TestRequireAdmin:
    def test_none_token(self):
        assert require_admin(None) is False
    def test_empty_token(self):
        assert require_admin('') is False
    def test_admin_token_returns_true(self, client, staff_token):
        assert require_admin(staff_token) is True
    def test_invalid_token(self):
        assert require_admin('invalid') is False


class TestAdminRequiredDecorator:
    def test_decorated_function_called_with_valid_token(self, client, staff_token):
        with client.application.test_request_context(headers={'X-Staff-Token': staff_token}):
            @admin_required
            def dummy():
                return jsonify({'ok': True})
            resp = dummy()
            assert resp.get_json()['ok'] is True

    def test_decorated_function_denied_no_token(self, client):
        with client.application.test_request_context():
            @admin_required
            def dummy():
                return jsonify({'ok': True})
            resp, status = dummy()
            assert status == 403

    def test_decorated_preserves_name(self):
        @admin_required
        def my_func():
            pass
        assert my_func.__name__ == 'my_func'
