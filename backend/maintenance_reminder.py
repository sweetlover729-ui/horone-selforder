# -*- coding: utf-8 -*-
"""
保养到期提醒守护线程
每日检查 maintenance_reminders 表，临近到期的自动发送通知

规则：
- 到期前 30 天：提醒客户预约保养
- 到期前 7 天：再次提醒
- 到期日当天：紧急提醒
- 过期 7 天后标记为 overdue
"""
import threading
import time
from datetime import datetime, timedelta

import database
from logging_config import get_logger

logger = get_logger('maintenance_reminder')

CHECK_INTERVAL_SEC = 3600  # 每小时检查一次

# 提醒时间窗口（天）
REMINDER_WINDOWS = [
    (30, '您的潜水设备 {equipment} 还有 30 天需进行年度保养，请提前预约。'),
    (7,  '您的潜水设备 {equipment} 还有 7 天需进行年度保养，请尽快预约。'),
    (0,  '您的潜水设备 {equipment} 今天需要进行年度保养！'),
]


def _check_and_remind(app=None):
    """检查临近到期的保养提醒并推送通知"""
    conn = None
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        now = datetime.now()

        # 标记过期 7 天的提醒
        cursor.execute('''
            UPDATE maintenance_reminders
            SET status = 'overdue', updated_at = NOW()
            WHERE status = 'pending'
              AND next_service_date < NOW() - INTERVAL '7 days'
        ''')
        conn.commit()

        # 查找需要提醒的记录
        for days, message_template in REMINDER_WINDOWS:
            target_date = now + timedelta(days=days)
            date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date_start + timedelta(days=1)

            cursor.execute('''
                SELECT mr.id, mr.order_id, mr.customer_id, mr.equipment_summary,
                       mr.next_service_date, c.phone, c.openid
                FROM maintenance_reminders mr
                LEFT JOIN customers c ON c.id = mr.customer_id
                WHERE mr.status = 'pending'
                  AND mr.next_service_date >= %s
                  AND mr.next_service_date < %s
            ''', (date_start, date_end))

            reminders = cursor.fetchall()
            for rem in reminders:
                message = message_template.format(equipment=rem['equipment_summary'])
                logger.info(f'保养提醒: customer={rem["customer_id"]} equipment={rem["equipment_summary"]} days={days}')

                # 如果通知模块已配置，尝试推送
                try:
                    from notification import NOTIFICATION_ENABLED, notify_status_change
                    if NOTIFICATION_ENABLED and rem.get('order_id'):
                        # 查找该订单的 order_no
                        cursor.execute('SELECT order_no FROM orders WHERE id=%s', (rem['order_id'],))
                        order_row = cursor.fetchone()
                        if order_row:
                            notify_status_change(
                                rem['order_id'], order_row['order_no'],
                                'maintenance_reminder',
                                customer_phone=rem.get('phone') or '',
                                customer_wechat_openid=rem.get('openid') or '',
                                extra={'equipment': rem['equipment_summary'],
                                       'next_date': str(rem['next_service_date'].date())}
                            )
                except ImportError:
                    pass  # notification module not available
                except Exception as e:
                    logger.warning(f'通知推送失败: {e}')

                # 当日提醒标记为已发送
                if days == 0:
                    cursor.execute('''
                        UPDATE maintenance_reminders
                        SET status = 'sent', reminder_sent = TRUE,
                            reminder_sent_at = NOW(), notify_count = notify_count + 1,
                            updated_at = NOW()
                        WHERE id = %s
                    ''', (rem['id'],))
                else:
                    cursor.execute('''
                        UPDATE maintenance_reminders
                        SET notify_count = notify_count + 1, updated_at = NOW()
                        WHERE id = %s
                    ''', (rem['id'],))
                conn.commit()

    except Exception as e:
        logger.error(f'保养提醒检查失败: {e}')
        if conn:
            try:
                conn.rollback()
            except:
                pass
    finally:
        if conn:
            database.release_connection(conn)


def start_reminder_daemon(app=None):
    """启动保养提醒守护线程"""

    def _daemon():
        logger.info('保养提醒守护线程已启动')
        while True:
            try:
                _check_and_remind(app)
            except Exception as e:
                logger.error(f'提醒线程异常: {e}')
            time.sleep(CHECK_INTERVAL_SEC)

    t = threading.Thread(target=_daemon, name='maintenance-reminder', daemon=True)
    t.start()
    logger.info(f'保养提醒守护线程已创建 (interval={CHECK_INTERVAL_SEC}s)')
