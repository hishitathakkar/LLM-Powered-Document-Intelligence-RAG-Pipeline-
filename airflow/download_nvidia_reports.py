from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import boto3
import os

S3_BUCKET = "big.data.ass.4"
NVIDIA_URL = "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx"

def scrape_and_upload_s3():
    response = requests.get(NVIDIA_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    
    reports = []
    for link in soup.find_all("a", href=True):
        if "pdf" in link["href"]:
            reports.append(link["href"])
    
    s3 = boto3.client("s3")
    
    for report_url in reports[:20]:  # Limit to 5 years (4 per year)
        report_name = report_url.split("/")[-1]
        pdf_content = requests.get(report_url).content

        with open(report_name, "wb") as f:
            f.write(pdf_content)
        
        s3.upload_file(report_name, S3_BUCKET, f"nvidia_reports/{report_name}")
        os.remove(report_name)

default_args = {
    "owner": "airflow",
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
}

with DAG(
    "nvidia_report_ingestion",
    default_args=default_args,
    schedule_interval="0 12 * * 1",  # Runs every Monday at noon
    catchup=False,
) as dag:
    download_task = PythonOperator(
        task_id="download_upload_s3",
        python_callable=scrape_and_upload_s3,
    )

    download_task
