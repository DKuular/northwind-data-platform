"""
Утилиты для работы с PostgreSQL
"""
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.exceptions import AirflowFailException
import logging

logger = logging.getLogger(__name__)

def get_db_connection(conn_id='postgres_default'):
    """
    Получение безопасного подключения к БД
    
    Args:
        conn_id: Идентификатор подключения в Airflow
    
    Returns:
        PostgresHook: Объект для работы с БД
    """
    try:
        hook = PostgresHook(postgres_conn_id=conn_id)
        logger.info(f"✅ Подключение к БД '{conn_id}' установлено")
        return hook
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к БД '{conn_id}': {e}")
        raise AirflowFailException(f"Не удалось подключиться к БД: {e}")

def execute_query(sql, parameters=None, conn_id='postgres_default'):
    """
    Безопасное выполнение SQL запроса
    
    Args:
        sql: SQL запрос
        parameters: Параметры для запроса (защита от SQL injection)
        conn_id: Идентификатор подключения
    
    Returns:
        Результат запроса
    """
    hook = get_db_connection(conn_id)
    
    try:
        if parameters:
            result = hook.get_first(sql, parameters=parameters)
        else:
            result = hook.get_first(sql)
        
        logger.debug(f"Запрос выполнен: {sql[:100]}...")
        return result
    except Exception as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        raise

def get_table_count(table_name, conn_id='postgres_default'):
    """Получение количества записей в таблице"""
    sql = f"SELECT COUNT(*) FROM {table_name}"
    result = execute_query(sql, conn_id=conn_id)
    return result[0] if result else 0
