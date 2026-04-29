"""
Token自动清理 — 守护线程，每小时清理过期token
作为Flask服务的一部分运行，不依赖OpenClaw或其他外部调度
"""
import threading
import time
from logging_config import get_logger

logger = get_logger('token_cleaner')

CLEANUP_INTERVAL_SEC = 3600  # 每小时清理一次

_cleaner_started = False
_lock = threading.Lock()


def _cleanup_loop(app):
    """后台清理循环 — daemon线程，随主进程终止"""
    # 启动后先等30秒，让DB连接池就绪
    time.sleep(30)
    logger.info("Token清理线程已启动，间隔=%ss", CLEANUP_INTERVAL_SEC)

    while True:
        try:
            from database import get_connection, release_connection
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute("DELETE FROM staff_tokens WHERE expires_at < NOW()")
            staff_deleted = cur.rowcount
            
            cur.execute("DELETE FROM customer_tokens WHERE expires_at < NOW()")
            cust_deleted = cur.rowcount
            
            conn.commit()
            release_connection(conn)
            
            if staff_deleted or cust_deleted:
                logger.info("Token清理: staff=%d, customer=%d", staff_deleted, cust_deleted)
        except Exception as e:
            logger.warning("Token清理异常(不影响服务): %s", e)
        
        time.sleep(CLEANUP_INTERVAL_SEC)


def start_cleaner(app):
    """启动后台token清理线程（幂等 — 仅启动一次）"""
    global _cleaner_started
    with _lock:
        if _cleaner_started:
            return
        _cleaner_started = True
    
    t = threading.Thread(target=_cleanup_loop, args=(app,), daemon=True)
    t.start()
    logger.info("Token自动清理守护线程已注册")
