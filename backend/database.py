# -*- coding: utf-8 -*-
"""
数据库连接（PostgreSQL，-w 1 单 worker 友好）
每个请求创建独立连接，函数结束时关闭。
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import hashlib
import hmac
import bcrypt
from logging_config import get_logger

logger = get_logger('db')

PG_CONN_STRING = os.environ.get('DATABASE_URL', 'postgresql://wjjmac@/selforder?host=%2Ftmp')

# 项目根目录和上传目录（集中配置）
PROJECT_ROOT = os.environ.get('HORONE_ROOT', '/Users/wjjmac/localserver/horone.selforder')
UPLOAD_DIR = os.path.join(PROJECT_ROOT, 'uploads')
PDF_DIR = os.path.join(UPLOAD_DIR, 'pdfs')
ORDER_UPLOAD_DIR = os.path.join(UPLOAD_DIR, 'orders')

def get_connection():
    """获取数据库连接"""
    conn = psycopg2.connect(PG_CONN_STRING, cursor_factory=RealDictCursor)
    return conn

def release_connection(conn):
    """关闭连接（兼容连接池语义，保持接口统一）"""
    if conn:
        try:
            conn.close()
        except Exception as exc:  # pragma: no cover
            import logging  # pragma: no cover
            logging.getLogger('horone.db').warning('关闭数据库连接失败: %s', exc)  # pragma: no cover

def dict_conn():
    """获取连接的别名"""
    return get_connection()

def hash_password(password):
    """密码哈希（bcrypt）"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, password_hash):
    """验证密码（支持 bcrypt 和旧 SHA256 双验证）
    返回 (is_valid, needs_rehash)
    - is_valid: 密码是否正确
    - needs_rehash: 是否需要从 SHA256 升级到 bcrypt
    """
    # 先尝试 bcrypt
    try:
        if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
            print(f'[DEBUG] verify_password: hash_len={len(password_hash)} hash_{len(password_hash[:50])}={repr(password_hash[:50])}... pwd_len={len(password)}')
            _result = bcrypt.checkpw(password.encode(), password_hash.encode())
            print(f'[DEBUG] verify_password: bcrypt_checkpw={_result}')
            if _result:
                return (True, False)
            return (False, False)
    except Exception as e:  # pragma: no cover
        print(f'[DEBUG] verify_password: bcrypt EXCEPTION: {type(e).__name__}: {e}')  # pragma: no cover
        pass  # pragma: no cover

    # 回退 SHA256（使用 constant-time 比较，防止时序攻击）
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    if hmac.compare_digest(sha256_hash, password_hash):
        return (True, True)  # 正确但需要 rehash

    return (False, False)

def check_and_init():
    """检查 PostgreSQL 数据库是否就绪"""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM product_types LIMIT 1")
        cur.close()
        release_connection(conn)
        logger.info("PostgreSQL 数据库已就绪")
    except Exception as e:
        logger.error("数据库检查失败: %s", e)
        raise

if __name__ == '__main__':
    check_and_init()  # pragma: no cover
