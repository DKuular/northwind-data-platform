"""
Конфигурация для DAG
"""
from airflow.models import Variable

def get_config():
    """Получение конфигурации из Airflow Variables"""
    return {
        'db_conn_id': Variable.get('DB_CONN_ID', default_var='postgres_default'),
        'validation_threshold_days': int(Variable.get('VALIDATION_THRESHOLD_DAYS', default_var='365')),
        'alert_enabled': Variable.get('ALERT_ENABLED', default_var='false').lower() == 'true',
    }

def get_alert_config():
    """Конфигурация алертов"""
    return {
        'alert_on_failure': Variable.get('ALERT_ON_FAILURE', default_var='true').lower() == 'true',
        'alert_on_success': Variable.get('ALERT_ON_SUCCESS', default_var='false').lower() == 'true',
    }