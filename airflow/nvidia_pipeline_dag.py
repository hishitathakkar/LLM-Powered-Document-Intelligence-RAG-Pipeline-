from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Task implementations from your uploaded modules
from upload_pdf_operator import upload_pdf
from pdf_parser_operator import parse_pdf
from plugins.chunking_operator import chunk_pdf
from embedding_operator import embed_chunks
from storage_operator import store_embeddings
from parsers.mistralocr import process_pdf
from rag.rag_chroma import store_in_chroma
from plugins.chunking_operator import chunk_pdf

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'nvidia_rag_pipeline_dynamic_multi',
    default_args=default_args,
    description='Multi-PDF NVIDIA pipeline with OCR, chunking, RAG',
    schedule_interval='@weekly',
    catchup=False
)

# Step 1: Upload or fetch PDF
upload_task = PythonOperator(
    task_id='upload_or_fetch_pdf',
    python_callable=upload_pdf,
    provide_context=True,
    params={"file_source": "local", "file_name": "sample.pdf"},  # adjust as needed
    dag=dag
)

# Step 2: Parse using OCR or another method
parse_task = PythonOperator(
    task_id='parse_pdf_text',
    python_callable=parse_pdf,
    provide_context=True,
    params={"parser": "mistral_ocr"},  # or "docling"
    dag=dag
)

# Step 3: Chunk the parsed text
chunk_task = PythonOperator(
    task_id='chunk_pdf_text',
    python_callable=chunk_pdf,
    provide_context=True,
    params={"strategy": "fixed"},  # or "tokens", "semantic"
    dag=dag
)

# Step 4: Embed the chunks
embed_task = PythonOperator(
    task_id='embed_chunks',
    python_callable=embed_chunks,
    params={"method": "chromadb"},  # or "pinecone", "manual"
    dag=dag
)

# Step 5: Store the embeddings
store_task = PythonOperator(
    task_id='store_embeddings',
    python_callable=store_embeddings,
    params={"rag_method": "chromadb"},  # or "pinecone", etc.
    dag=dag
)

# DAG Task Order
upload_task >> parse_task >> chunk_task >> embed_task >> store_task

# DAG Task Order
upload_task >> parse_task >> chunk_task >> embed_task >> store_task
