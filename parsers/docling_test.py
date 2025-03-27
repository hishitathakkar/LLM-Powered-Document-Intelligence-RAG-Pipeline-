import os
import time
import requests
import docling  # Import Docling for PDF parsing
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowFailException
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base import BaseHook
import json
from datetime import datetime, timedelta

# Load configuration
with open('/opt/airflow/config/nvidia_config.json') as config_file:
    config = json.load(config_file)

# S3 Configuration
AWS_CONN_ID = config['AWS_CONN_ID']
aws_creds = BaseHook.get_connection(AWS_CONN_ID)
BUCKET_NAME = config['BUCKET_NAME']
AWS_ACCESS_KEY = aws_creds.login  
AWS_SECRET_KEY = aws_creds.password  
S3_BASE_FOLDER = config['S3_BASE_FOLDER']
RESULTS_FOLDER = config['RESULTS_FOLDER']
TEMP_DATA_FOLDER = config['TEMP_DATA_FOLDER']
BASE_URL = config['BASE_URL']

# Default DAG arguments
default_args = {
    "owner": config['default_args']['owner'],
    "depends_on_past": config['default_args']['depends_on_past'],
    "start_date": datetime.fromisoformat(config['default_args']['start_date']),
    "retries": config['default_args']['retries'],
    "retry_delay": timedelta(minutes=int(config['default_args']['retry_delay'].split(':')[1]))
}

dag = DAG(
    "nvidia_quarterly_reports_pipeline",
    default_args=default_args,
    description="Scrape, download, parse, and upload NVIDIA quarterly reports",
    schedule_interval='@daily',
    catchup=False,
)

# =========================
# PDF PARSING FUNCTION
# =========================

def parse_pdf_with_docling(pdf_path):
    """
    Uses Docling to parse a given PDF and extract structured content.
    """
    print(f"Parsing PDF: {pdf_path}")
    try:
        doc = docling.Document(pdf_path)  # Load the PDF
        text = doc.text()  # Extract plain text
        tables = doc.tables()  # Extract tables if available
        
        output = {
            "text": text,
            "tables": tables
        }
        
        # Save parsed content as JSON
        json_filename = pdf_path.replace(".pdf", ".json")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=4)
        
        print(f"Extracted content saved to: {json_filename}")
        return json_filename
    
    except Exception as e:
        print(f"Error parsing PDF {pdf_path}: {e}")
        return None

# =========================
# MAIN PROCESSING FUNCTION
# =========================

def process_pdfs_and_upload(**context):
    """
    1. Retrieve downloaded PDFs
    2. Parse using Docling
    3. Upload JSON results to S3
    """
    year_folder = context['task_instance'].xcom_pull(task_ids='nvidia_scrape_download', key='year_folder')

    if not year_folder or not os.path.exists(year_folder):
        raise AirflowFailException("No downloaded PDFs found for processing.")

    s3_hook = S3Hook(aws_conn_id=AWS_CONN_ID)
    parsed_files = []

    for file_name in os.listdir(year_folder):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(year_folder, file_name)
            json_path = parse_pdf_with_docling(pdf_path)

            if json_path:
                s3_key = f"{S3_BASE_FOLDER}/parsed_reports/{os.path.basename(json_path)}"
                s3_hook.load_file(json_path, key=s3_key, bucket_name=BUCKET_NAME, replace=True)
                print(f"Uploaded {json_path} to S3: {s3_key}")
                parsed_files.append(json_path)

    if not parsed_files:
        raise AirflowFailException("No PDFs successfully parsed and uploaded.")

# =========================
# DEFINE AIRFLOW TASKS
# =========================

parse_and_upload_task = PythonOperator(
    task_id="parse_and_upload_pdfs",
    python_callable=process_pdfs_and_upload,
    provide_context=True,
    dag=dag,
)

parse_and_upload_task
