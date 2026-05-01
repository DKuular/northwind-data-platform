"""
Функции валидации данных
"""
from postgres_utils import execute_query
import logging

logger = logging.getLogger(__name__)

def validate_orders(conn_id='postgres_default'):
    """
    Валидация данных в таблице orders
    
    Returns:
        dict: Результаты валидации
    """
    sql = """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN order_date IS NULL THEN 1 END) as null_dates,
            COUNT(CASE WHEN shipped_date < order_date THEN 1 END) as invalid_shipments,
            MIN(order_date) as min_date,
            MAX(order_date) as max_date
        FROM orders
    """
    
    result = execute_query(sql, conn_id=conn_id)
    
    return {
        'total_orders': result[0],
        'null_dates': result[1],
        'invalid_shipments': result[2],
        'min_date': str(result[3]) if result[3] else None,
        'max_date': str(result[4]) if result[4] else None,
    }

def check_date_range(threshold_days=365, conn_id='postgres_default'):
    """
    Проверка актуальности данных
    
    Args:
        threshold_days: Порог в днях (данные не старше X дней)
        conn_id: Идентификатор подключения
    """
    sql = """
        SELECT 
            MAX(order_date) as max_date,
            COUNT(CASE WHEN order_date > CURRENT_DATE - INTERVAL '%s days' THEN 1 END) as recent_orders
        FROM orders
    """
    
    result = execute_query(sql, parameters=(threshold_days,), conn_id=conn_id)
    
    return {
        'max_date': str(result[0]) if result[0] else None,
        'recent_orders': result[1] if result[1] else 0,
    }

def validate_row_level_security():
    """Проверка RLS для разных ролей"""
    roles = ['airflow_user', 'spark_reader', 'bi_reader']
    results = {}
    
    for role in roles:
        conn_id = f'postgres_{role}'
        try:
            result = execute_query("SELECT COUNT(*) FROM customers LIMIT 1", conn_id=conn_id)
            results[role] = 'SUCCESS'
        except Exception as e:
            results[role] = f'FAILED: {str(e)[:50]}'
    
    return results