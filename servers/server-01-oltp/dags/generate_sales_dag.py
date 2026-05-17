"""
DAG для генерации продаж Northwind
- Догоняет пропущенные календарные дни до «вчера» (полные дневные объёмы).
- В каждый запуск добавляет небольшую партию заказов за сегодня (по умолчанию только Пн–Пт).
Расписание: каждые 20 минут, круглосуточно.

Параметр ignore_working_days (ручной запуск):
- В UI: Trigger DAG w/ config → JSON: {"ignore_working_days": true}
- Либо задать в params DAG (по умолчанию false); при ручном запуске конфиг перекрывает params.

Версия 1.3.0
"""

import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, '/opt/airflow/dags_modules')

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import logging

from sales_generator import (
    get_last_order_date,
    get_existing_references,
    generate_orders_for_date_range,
    generate_intraday_orders_today,
    insert_orders_to_db,
    get_generation_stats,
)

logger = logging.getLogger(__name__)


def _truthy_run_param(value):
    """Булево из conf/params (JSON/UI может отдать bool, строку или число)."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'on')
    return bool(value)


def resolve_ignore_working_days(**context):
    """True — генерировать и в выходные. Приоритет: dag_run.conf → params DAG."""
    dr = context.get('dag_run')
    conf = (dr.conf if dr else None) or {}
    params = context.get('params') or {}
    if 'ignore_working_days' in conf:
        return _truthy_run_param(conf.get('ignore_working_days'))
    return _truthy_run_param(params.get('ignore_working_days', False))


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
    Догоняет дни до вчера (полный дневной объём) и на каждый тик добавляет партию за сегодня.
    """
    hook = PostgresHook(postgres_conn_id='postgres_default')
    ignore_wd = resolve_ignore_working_days(**context)
    last_date = get_last_order_date(hook)
    today = datetime.now().date()

    logger.info(f"📅 ignore_working_days={ignore_wd}")
    logger.info(f"📅 Последняя дата заказа в БД: {last_date}")
    logger.info(f"📅 Сегодня: {today}")

    if last_date is None:
        gap_start = datetime(2020, 1, 1).date()
        logger.info(f"⚠️ Нет заказов в БД. Догон с {gap_start}")
    else:
        gap_start = last_date + timedelta(days=1)

    refs = get_existing_references(hook)
    created_total = 0
    amount_total = 0.0

    # Пропущенные календарные дни строго до сегодня (сегодня — только внутридневными партиями)
    if gap_start < today:
        backfill_end = today - timedelta(days=1)
        logger.info(f"🚀 Догон заказов с {gap_start} по {backfill_end}")
        orders_bf = generate_orders_for_date_range(
            hook, refs, gap_start, backfill_end, ignore_working_days=ignore_wd
        )
        if orders_bf:
            c, a = insert_orders_to_db(hook, orders_bf)
            created_total += c
            amount_total += a
            logger.info(f"✅ Догон: {c} заказов на ${a:,.2f}")

    # Каждый запуск — небольшая партия за сегодня (Пн–Пт)
    orders_in = generate_intraday_orders_today(
        hook, refs, today, ignore_working_days=ignore_wd
    )
    if orders_in:
        c, a = insert_orders_to_db(hook, orders_in)
        created_total += c
        amount_total += a
        logger.info(f"✅ Сегодня (партия): {c} заказов на ${a:,.2f}")

    if created_total == 0:
        logger.info("Заказов для вставки не было (например, выходной).")
        return

    logger.info(f"✅ Всего за запуск: {created_total} заказов на ${amount_total:,.2f}")
    context['ti'].xcom_push(key='orders_created', value=created_total)
    context['ti'].xcom_push(key='total_amount', value=amount_total)

def show_stats(**context):
    """Вывод статистики"""
    hook = PostgresHook(postgres_conn_id='postgres_default')
    stats = get_generation_stats(hook)
    
    logger.info("=" * 60)
    logger.info("📊 СТАТИСТИКА БАЗЫ ДАННЫХ NORTHWIND")
    logger.info(f"   Всего заказов: {stats['total_orders']:,}")
    logger.info(f"   Первый заказ: {stats['first_order']}")
    logger.info(f"   Последний заказ: {stats['last_order']}")
    logger.info("=" * 60)

# Создание DAG
with DAG(
    'generate_northwind_sales',
    default_args=default_args,
    description='Northwind: догон по дням + внутридневные партии по расписанию',
    schedule_interval='*/20 * * * *',
    catchup=False,
    tags=['sales', 'generation', 'northwind'],
    max_active_runs=1,
    params={
        'ignore_working_days': False,
    },
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