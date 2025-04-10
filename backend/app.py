from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import os
import io
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import BytesIO
from tempfile import NamedTemporaryFile
import boto3
from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from redis import Redis
from litellm import completion
from dotenv import load_dotenv
from redis_streams import redis_files
from chunking import recursive_character_split, token_text_split, semantic_split
from rag_naive import naive_rag_search
from rag_pinecone import store_in_pinecone, query_pinecone
from rag_chroma import store_in_chroma, query_chroma
from docling.extract import Extractor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

app = FastAPI()

# Initialize Redis connection
redis_client = Redis(host='localhost', port=6379, db=0)

load_dotenv(r'Add\Path\to\environment\access.env')

# Set API key directly
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')

# AWS S3 config
s3 = boto3.client("s3")
BUCKET_NAME = "assignment4part2"
BASE_URL = "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx"
YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

@app.post("/upload_pdf")
async def pdf_upload(file: UploadFile = File(...)):
    MAX_FILE_SIZE = 3 * 1024 * 1024
    pdf_name = file.filename

    if not pdf_name.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    try:
        file_content = await file.read()

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 3MB limit")

        redis_client.delete("pdf_content", "markdown_content", "chunked_content", "pdf_method")
        redis_client.set("pdf_content", file_content)

        return {"message": "File uploaded successfully and cached in Redis stream"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/pdf_parser")
async def pdf_parser(selected_parser: str):
    try:
        file = redis_files()
        # Add the call to Docling and Mistral Code here

        redis_client.delete("pdf_content", "markdown_content", "chunked_content")
        redis_client.set("markdown_content", markdown_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")

@app.get("/chunking_strat")
async def pdf_parser(selected_chunk: str):
    try:
        file = redis_files()
        if selected_chunk == "recursive":
            chunked_content = recursive_character_split(file.decode("utf-8"))
        elif selected_chunk == "token":
            chunked_content = token_text_split(file.decode("utf-8"))
        elif selected_chunk == "semantic":
            chunked_content = semantic_split(file.decode("utf-8"))
        else:
            raise HTTPException(status_code=400, detail="Invalid chunking strategy.")

        redis_client.delete("pdf_content", "markdown_content", "chunked_content")
        redis_client.set("chunked_content", str(chunked_content))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")

@app.get("/rag_method")
async def pdf_parser(selected_rag: str, chunking_strategy: str = Query("recursive")):
    try:
        file = redis_files()
        documents = [file.decode("utf-8")]
        quarters = ["Q1"]

        if selected_rag == "pinecone":
            store_in_pinecone(documents, quarters, chunking_strategy)
        elif selected_rag == "chroma":
            store_in_chroma(documents, quarters, chunking_strategy)
        elif selected_rag == "naive":
            pass
        else:
            raise HTTPException(status_code=400, detail="Invalid RAG method.")

        return {"message": f"RAG method {selected_rag} applied with {chunking_strategy} chunking."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")

@app.get("/ask_question")
async def ask_question(question: str, selected_year: str, selected_quarter: str):
    try:
        context = "No relevant context found."

        results = query_chroma(question, quarter_filter=selected_quarter)
        if results:
            context = "\n".join([res["text"] for res in results])

        messages = [
            {"role": "assistant", "content": context},
            {"role": "user", "content": f'{question}. Give your response based solely on the context provided. Do not make up information.'}
        ]

        response = completion(model='GPT-4o', messages=messages)
        json_response = jsonable_encoder(response)
        return JSONResponse(content=json_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")

@app.get("/pricing")
async def model_pricing(input_tokens: int, output_tokens: int):
    input_tokens_total = input_tokens * (2.50 / 1000000)
    output_tokens_total = output_tokens * (10 / 1000000)
    total = input_tokens_total + output_tokens_total
    total = round(total, 4)
    return JSONResponse(content={"total_value": total}, media_type="application/json")

@app.post("/ingest_from_s3")
async def ingest_s3_file(filename: str, chunking_strategy: str = "recursive", rag_method: str = "pinecone"):
    try:
        s3_key = f"nvidia_financials/parsed/{filename}.json"
        with NamedTemporaryFile(delete=False, suffix=".json") as tmp_file:
            s3.download_file(BUCKET_NAME, s3_key, tmp_file.name)
            tmp_file.seek(0)
            parsed_json = json.load(tmp_file)

        parsed_text = " ".join([block["text"] for block in parsed_json["content"] if block.get("text")])
        documents = [parsed_text]

        match = re.search(r"(Q[1-4])[_-]?(20\\d{2})", filename)
        quarter = f"{match.group(1)}-{match.group(2)}" if match else "auto"
        quarters = [quarter]

        if rag_method == "pinecone":
            store_in_pinecone(documents, quarters, chunking_strategy)
        elif rag_method == "chroma":
            store_in_chroma(documents, quarters, chunking_strategy)
        elif rag_method == "naive":
            return {"message": "Naive RAG is used at query-time only."}
        else:
            raise HTTPException(status_code=400, detail="Invalid RAG method.")

        return {
            "message": f"Ingested {filename}.json from S3 using {rag_method} with {chunking_strategy} chunking."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing S3 file: {str(e)}")

@app.get("/scrape_nvidia")
def scrape_nvidia_pdfs():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0"
        }

        response = requests.get(BASE_URL, headers=headers)
        if response.status_code != 200:
            return {"message": f"Failed to fetch page: {response.status_code}"}

        soup = BeautifulSoup(response.content, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.lower().endswith(".pdf"):
                pdf_url = urljoin(BASE_URL, href)
                link_text = link.get_text(strip=True)
                pdf_name = href.split("/")[-1]

                if any(year in link_text or year in pdf_name for year in YEARS) and \
                   any(qtr in link_text or qtr in pdf_name for qtr in QUARTERS):
                    download_parse_upload_pdf(pdf_url, BUCKET_NAME, pdf_name)

        return {"message": "Scraping and upload complete."}

    except Exception as e:
        return {"message": f"Error scraping PDFs: {str(e)}"}

def download_parse_upload_pdf(pdf_url, bucket_name, pdf_name):
    try:
        response = requests.get(pdf_url, stream=True)
        if response.status_code == 200:
            pdf_buffer = BytesIO(response.content)
            extractor = Extractor()
            parsed_content = extractor.parse(pdf_buffer)
            parsed_text = parsed_content.to_json()

            s3_pdf_path = f"nvidia_financials/{pdf_name}"
            s3_text_path = f"nvidia_financials/parsed/{pdf_name.replace('.pdf', '.json')}"

            s3_hook = S3Hook(aws_conn_id="aws_default")
            s3_hook.get_conn().upload_fileobj(pdf_buffer, bucket_name, s3_pdf_path)
            s3_hook.get_conn().put_object(Bucket=bucket_name, Key=s3_text_path, Body=parsed_text)

    except Exception as e:
        print(f"Error processing {pdf_url}: {e}")
