from airflow.operators.python import PythonOperator
from airflow import DAG
from datetime import datetime
from webscrape_nvidia import download_report  # adjust the import

with DAG(dag_id='nvidia_pipeline',
         start_date=datetime(2024, 1, 1),
         schedule_interval=None,
         catchup=False) as dag:

    download_pdf = PythonOperator(
        task_id='download_pdf',
        python_callable=download_report,
        provide_context=True,
    )
