"""Tests for database module"""
import pytest
import database


class TestHashPassword:
    def test_hash_returns_string(self):
        result = database.hash_password('test123')
        assert isinstance(result, str)
        assert len(result) > 20
    def test_hash_starts_with_bcrypt_prefix(self):
        result = database.hash_password('hello')
        assert result.startswith('$2b$') or result.startswith('$2a$')
    def test_hash_deterministic_for_same_password(self):
        h1 = database.hash_password('samepass')
        h2 = database.hash_password('samepass')
        assert h1 != h2  # bcrypt uses random salt, so different each time


class TestVerifyPassword:
    def test_correct_password(self):
        h = database.hash_password('correct')
        ok, _ = database.verify_password('correct', h)
        assert ok is True
    def test_wrong_password(self):
        h = database.hash_password('correct')
        ok, _ = database.verify_password('wrong', h)
        assert ok is False
    def test_empty_password(self):
        h = database.hash_password('correct')
        ok, _ = database.verify_password('', h)
        assert ok is False


class TestGetConnection:
    def test_returns_connection(self):
        conn = database.get_connection()
        assert conn is not None
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        assert cursor.fetchone()['?column?'] == 1
        database.release_connection(conn)
    def test_connection_is_usable(self):
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT current_database()')
        assert cursor.fetchone() is not None
        database.release_connection(conn)


class TestReleaseConnection:
    def test_release_closes_connection(self):
        conn = database.get_connection()
        database.release_connection(conn)
        try:
            conn.cursor()
            closed = False
        except Exception:
            closed = True
        assert closed
