from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
}

with DAG(
    'test_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='Test DAG'
) as dag:
    
    task = BashOperator(
        task_id='print_date',
        bash_command='date'
    )