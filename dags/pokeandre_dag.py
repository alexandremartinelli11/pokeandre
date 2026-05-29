import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

# Adiciona o diretório /opt/airflow ao sys.path para que o Python encontre o módulo 'src'
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Importando os módulos ETL do projeto
from src.etl.extract import extract_pokemon_data
from src.etl.transform import transform_pokemon_data
from src.etl.quality import validate_quality
from src.etl.load import load_pokemon_data

# Definição dos argumentos padrão da DAG
default_args = {
    'owner': 'pokeandre',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Declaração da DAG
with DAG(
    'pokeandre_etl_pipeline',
    default_args=default_args,
    description='Pipeline ETL PokeAndre: Extração, Transformação, Qualidade e Carga',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['pokeandre', 'etl'],
) as dag:

    # Task 1: Extract
    extract_task = PythonOperator(
        task_id='extract_task',
        python_callable=extract_pokemon_data,
    )

    # Task 2: Transform
    transform_task = PythonOperator(
        task_id='transform_task',
        python_callable=transform_pokemon_data,
    )

    # Task 3: Quality Check
    quality_task = PythonOperator(
        task_id='quality_task',
        python_callable=validate_quality,
    )

    # Task 4: Load
    load_task = PythonOperator(
        task_id='load_task',
        python_callable=load_pokemon_data,
    )

    # Definição das dependências (ordem de execução)
    extract_task >> transform_task >> quality_task >> load_task
