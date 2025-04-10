import os
import io
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from docling.extract import Extractor
from io import BytesIO
import boto3

from chunking import recursive_character_split, token_text_split, semantic_split
from rag_naive import naive_rag_search
from rag_pinecone import store_in_pinecone
from rag_chroma import store_in_chroma

# Config
BASE_URL = "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx"
BUCKET_NAME = "assignment4part2"
YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

# Boto3 S3 client
s3 = boto3.client("s3")

def scrape_nvidia_pdfs(rag_method="pinecone", chunking_strategy="recursive"):
    """Scrape PDFs, parse with Docling, upload to S3, and pass through RAG pipeline."""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }

    response = requests.get(BASE_URL, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch page: {response.status_code}")
        return

    print("✅ Webpage fetched successfully.")
    soup = BeautifulSoup(response.content, "html.parser")

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.lower().endswith(".pdf"):
            pdf_url = urljoin(BASE_URL, href)
            link_text = link.get_text(strip=True)
            pdf_name = href.split("/")[-1]

            if any(year in link_text or year in pdf_name for year in YEARS) and \
               any(qtr in link_text or qtr in pdf_name for qtr in QUARTERS):
                print(f"📄 Match found: {pdf_name}")
                download_parse_upload_pdf(pdf_url, BUCKET_NAME, pdf_name, rag_method, chunking_strategy)

def download_parse_upload_pdf(pdf_url, bucket_name, pdf_name, rag_method, chunking_strategy):
    try:
        response = requests.get(pdf_url, stream=True)
        if response.status_code != 200:
            print(f"❌ Failed to download {pdf_url}")
            return

        pdf_buffer = BytesIO(response.content)

        # 🧠 Parse with Docling
        extractor = Extractor()
        parsed_content = extractor.parse(pdf_buffer)
        parsed_text = parsed_content.to_json()

        # Upload raw PDF to S3
        s3_pdf_path = f"nvidia_financials/{pdf_name}"
        s3.upload_fileobj(BytesIO(response.content), bucket_name, s3_pdf_path)

        # Upload parsed JSON to S3
        parsed_key = f"nvidia_financials/parsed/{pdf_name.replace('.pdf', '.json')}"
        s3.put_object(Bucket=bucket_name, Key=parsed_key, Body=parsed_text)

        print(f"✅ Uploaded {pdf_name} and parsed JSON to S3.")

        # 🧠 Run RAG Pipeline
        parsed_json = json.loads(parsed_text)
        full_text = " ".join([b["text"] for b in parsed_json["content"] if b.get("text")])
        documents = [full_text]

        match = re.search(r"(Q[1-4])[_-]?(20\\d{2})", pdf_name)
        quarter = f"{match.group(1)}-{match.group(2)}" if match else "auto"
        quarters = [quarter]

        if rag_method == "pinecone":
            store_in_pinecone(documents, quarters, chunking_strategy)
        elif rag_method == "chroma":
            store_in_chroma(documents, quarters, chunking_strategy)
        elif rag_method == "naive":
            print("ℹ️ Naive RAG does not persist vectors.")
        else:
            print("⚠️ Invalid RAG method specified.")

    except Exception as e:
        print(f"❌ Error processing {pdf_url}: {e}")
