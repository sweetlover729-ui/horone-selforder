"""
数据库自动备份 — 守护线程，每日凌晨4点自动备份
作为Flask服务的一部分运行，不依赖OpenClaw或其他外部调度
"""
import threading
import time
import subprocess
import os
import glob
from datetime import datetime, timedelta
from logging_config import get_logger

logger = get_logger('backup_scheduler')

BACKUP_DIR = os.path.expanduser('~/selforderbackup260425')
RETENTION_DAYS = 7
BACKUP_HOUR = 4  # 凌晨4点

_scheduler_started = False
_lock = threading.Lock()
_last_backup_date = None  # 防止同一天多次执行


def _run_backup():
    """执行一次数据库备份"""
    today = datetime.now().strftime('%Y%m%d')
    filename = f'backup_{today}.sql'
    filepath = os.path.join(BACKUP_DIR, filename)
    
    # 确保备份目录存在
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    logger.info("开始数据库备份 → %s", filepath)
    
    try:
        result = subprocess.run(
            ['pg_dump', '-h', '/tmp', 'selforder'],
            capture_output=True, text=True, timeout=300
        )
        
        if result.returncode == 0:
            with open(filepath, 'w') as f:
                f.write(result.stdout)
            
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            logger.info("备份完成: %s (%.1f MB)", filename, size_mb)
        else:
            logger.error("pg_dump失败: %s", result.stderr.strip())
            return False
        
        # 清理7天前的旧备份
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        for old_file in glob.glob(os.path.join(BACKUP_DIR, 'backup_*.sql')):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(old_file))
                if mtime < cutoff:
                    os.remove(old_file)
                    logger.info("清理旧备份: %s", os.path.basename(old_file))
            except OSError as e:
                logger.warning("清理旧备份失败: %s → %s", old_file, e)
        
        return True
        
    except subprocess.TimeoutExpired:
        logger.error("pg_dump超时(>300s)")
        return False
    except Exception as e:
        logger.error("备份异常: %s", e)
        return False


def _backup_loop(app):
    """后台备份循环 — daemon线程"""
    global _last_backup_date
    
    # 启动后等60秒让服务就绪
    time.sleep(60)
    logger.info("数据库备份调度线程已启动，每日 %02d:00 CST", BACKUP_HOUR)
    
    while True:
        try:
            now = datetime.now()
            today = now.date()
            
            # 检查是否到了备份时间
            if (now.hour == BACKUP_HOUR 
                and _last_backup_date != today):
                _last_backup_date = today  # pragma: no cover
                _run_backup()  # pragma: no cover
              # pragma: no cover
        except Exception as e:  # pragma: no cover
            logger.warning("备份调度异常(不影响服务): %s", e)  # pragma: no cover
        
        time.sleep(60)  # 每分钟检查一次


def start_backup_scheduler(app):
    """启动后台备份调度线程（幂等 — 仅启动一次）"""
    global _scheduler_started
    with _lock:
        if _scheduler_started:
            return
        _scheduler_started = True
    
    t = threading.Thread(target=_backup_loop, args=(app,), daemon=True)
    t.start()
    logger.info("数据库自动备份守护线程已注册")
