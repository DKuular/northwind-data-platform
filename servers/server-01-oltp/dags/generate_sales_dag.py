"""
DAG для генерации продаж Northwind
Генерация от последней даты в БД до сегодня
Расписание: каждые 20 минут с 10:00 до 19:00

Версия 1.0.8
"""

import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, '/opt/airflow/dags_modules')

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowSkipException  # ← ДОБАВИТЬ ЭТОТ ИМПОРТ
from datetime import datetime, timedelta
import logging

from sales_generator import (
    get_last_order_date,
    get_existing_references,
    generate_orders_for_date_range,
    insert_orders_to_db,
    get_generation_stats
)

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2026, 5, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def check_and_generate(**context):
    """
    Проверка последней даты и генерация недостающих заказов
    """
    hook = PostgresHook(postgres_conn_id='postgres_default')
    
    # Последняя дата заказа в БД
    last_date = get_last_order_date(hook)
    today = datetime.now().date()
    
    logger.info(f"📅 Последняя дата заказа: {last_date}")
    logger.info(f"📅 Сегодня: {today}")
    
    # Если данных нет, начинаем с 2020-01-01
    if last_date is None:
        start_date = datetime(2020, 1, 1).date()
        logger.info(f"⚠️ Нет заказов в БД. Начинаем с {start_date}")
    else:
        start_date = last_date + timedelta(days=1)
    
    # Если нет пропущенных дней, пропускаем
    if start_date > today:
        logger.info(f"✅ Данные актуальны до {last_date}. Пропускаем.")
        raise AirflowSkipException("Нет новых дней для генерации")
    
    logger.info(f"🚀 Начинаем генерацию заказов с {start_date} по {today}")
    
    # Получаем справочные данные из Northwind
    refs = get_existing_references(hook)
    
    # Генерируем заказы
    orders = generate_orders_for_date_range(hook, refs, start_date, today)
    
    if not orders:
        logger.info("Нет заказов для вставки")
        return
    
    # Вставляем в БД
    created, total_amount = insert_orders_to_db(hook, orders)
    
    logger.info(f"✅ Создано {created} заказов на сумму ${total_amount:,.2f}")
    context['ti'].xcom_push(key='orders_created', value=created)
    context['ti'].xcom_push(key='total_amount', value=total_amount)

def show_stats(**context):
    """Вывод статистики"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    stats = get_generation_stats(hook)
    
    logger.info("=" * 60)
    logger.info("📊 СТАТИСТИКА БАЗЫ ДАННЫХ NORTHWIND")
    logger.info(f"   Всего заказов: {stats['total_orders']:,}")
    logger.info(f"   Общая сумма: ${stats['total_amount']:,.2f}")
    logger.info(f"   Первый заказ: {stats['first_order']}")
    logger.info(f"   Последний заказ: {stats['last_order']}")
    logger.info("=" * 60)

# Создание DAG
with DAG(
    'generate_northwind_sales',
    default_args=default_args,
    description='Генерация продаж Northwind от последней даты до сегодня',
    schedule_interval='*/20 10-19 * * *',  # Каждые 20 минут с 10:00 до 19:00
    catchup=False,
    tags=['sales', 'generation', 'northwind'],
    max_active_runs=1,
) as dag:
    
    generate = PythonOperator(
        task_id='generate_orders',
        python_callable=check_and_generate,
    )
    
    stats = PythonOperator(
        task_id='show_stats',
        python_callable=show_stats,
    )
    
    generate >> stats