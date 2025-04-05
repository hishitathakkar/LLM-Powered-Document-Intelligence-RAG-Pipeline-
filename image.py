from diagrams import Cluster, Diagram
from diagrams.aws.compute import ECS
from diagrams.aws.ml import Sagemaker
from diagrams.onprem.mlops import Mlflow
from diagrams.onprem.workflow import Airflow
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.client import Users
from diagrams.programming.language import Python
from diagrams.custom import Custom

with Diagram("LLM-Powered RAG Pipeline", direction="LR"):

    user = Users("User")

    with Cluster("Frontend"):
        streamlit = Custom("Streamlit", "./icons/streamlit.png")
        fastapi = Custom("FastAPI", "./icons/fastapi.png")
        user >> streamlit >> fastapi

    with Cluster("Data Pipeline (Airflow)"):
        airflow = Airflow("Apache Airflow")
        scraper = Python("Scraper")
        parser_docling = Python("Docling Parser")
        parser_mistral = Python("Mistral OCR Parser")
        chunking = Python("Chunking Engine")
        embeddings = Python("Embedding (OpenAI)")
        airflow >> scraper >> [parser_docling, parser_mistral] >> chunking >> embeddings

    with Cluster("Vector Stores"):
        pinecone = Custom("Pinecone", "./icons/pinecone.png")
        chromadb = Custom("ChromaDB", "./icons/chroma.png")
        embeddings >> [pinecone, chromadb]

    with Cluster("RAG Retrieval"):
        naive = Python("Naive RAG (Manual Cosine)")
        hybrid = Python("Hybrid RAG")
        pinecone >> hybrid
        chromadb >> hybrid
        naive << embeddings

    with Cluster("Backend Services"):
        fastapi >> hybrid >> Python("LLM (GPT/Claude)")
        hybrid >> Python("Context Builder")

    with Cluster("Docker Containers"):
        docker1 = Custom("Airflow Container", "./icons/docker.png")
        docker2 = Custom("Streamlit+FastAPI Container", "./icons/docker.png")
        [docker1, docker2]

    fastapi >> docker2
    airflow >> docker1
