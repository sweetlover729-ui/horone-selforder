# -*- coding: utf-8 -*-
"""
Shared status change audit logger for state machine transitions.

Used by all blueprints (console / client / admin) to record
order status transitions in the status_change_log table.
"""
from logging_config import get_logger

logger = get_logger('status_log')


def log_status_change(conn, order_id, field, old_value, new_value, changed_by, changed_via='console'):
    """Record a state machine field transition (status / payment_status etc.).

    Args:
        conn:       psycopg2 connection (with RealDictCursor cursor).
        order_id:   int order id.
        field:      column name ('status' / 'payment_status').
        old_value:  previous value.
        new_value:  new value.
        changed_by: human-readable name of the person/system who made the change.
        changed_via: source (console / client / admin).
    """
    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO status_change_log '
            '(order_id, field, old_value, new_value, changed_by, changed_via) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (order_id, field, old_value, new_value, changed_by, changed_via)
        )
        conn.commit()
    except Exception as e:
        logger.warning('status_change_log insert failed for order %s: %s', order_id, e)
