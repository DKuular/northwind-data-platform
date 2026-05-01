"""
DAG для валидации данных orders
Использует модули из dags_modules/

Версия 1.0.2
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowFailException
from datetime import datetime, timedelta

# Импорт модулей
from postgres_utils import get_db_connection, get_table_count
from validators import validate_orders, check_date_range, validate_row_level_security
from alerts import send_telegram_alert, task_failure_alert
from config import get_config, get_alert_config

import logging
logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 10),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'on_failure_callback': task_failure_alert,
}

def validate_task(**context):
    """Задача валидации"""
    config = get_config()
    
    # Валидация
    result = validate_orders(conn_id=config['db_conn_id'])
    logger.info(f"✅ Результаты: {result}")
    
    # Проверка условий
    if result['null_dates'] > 0:
        raise AirflowFailException(f"❗Найдено {result['null_dates']} заказов с пустыми датами")
    
    if result['invalid_shipments'] > 0:
        raise AirflowFailException(f"❗Найдено {result['invalid_shipments']} некорректных доставок")
    
    return result

def date_range_check(**context):
    """Проверка актуальности данных"""
    config = get_config()
    result = check_date_range(
        threshold_days=config['validation_threshold_days'],
        conn_id=config['db_conn_id']
    )
    logger.info(f"✅ Актуальность: {result}")
    return result

def rls_check_task(**context):
    """Проверка RLS"""
    result = validate_row_level_security()
    logger.info(f"❗ RLS: {result}")
    return result

with DAG(
    'validate_orders_dates',
    default_args=default_args,
    description='Валидация данных orders',
    schedule_interval='0 8 * * *',
    catchup=False,
    tags=['validation', 'orders'],
) as dag:
    
    validate = PythonOperator(
        task_id='validate_orders',
        python_callable=validate_task,
    )
    
    check_date = PythonOperator(
        task_id='check_date_range',
        python_callable=date_range_check,
    )
    
    check_rls = PythonOperator(
        task_id='check_row_level_security',
        python_callable=rls_check_task,
    )
    
    validate >> check_date >> check_rls