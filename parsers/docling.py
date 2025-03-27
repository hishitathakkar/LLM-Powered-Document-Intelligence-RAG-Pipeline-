import os
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from docling.extract import Extractor

# Base URL for NVIDIA investor relations
BASE_URL = "https://investor.nvidia.com/financial-info/quarterly-results/default.aspx"

# AWS S3 bucket name
BUCKET_NAME = "assignment4part2"

# Define the years and quarters to scrape
YEARS = ["2020", "2021", "2022", "2023", "2024", "2025"]
QUARTERS = ["Q1", "Q2", "Q3", "Q4"]

def scrape_nvidia_pdfs(base_url, bucket_name):
    """Scrape NVIDIA quarterly PDFs and upload them to S3."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0"
    }
    
    # Request webpage
    response = requests.get(base_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return
    print("Webpage fetched successfully!")

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all links
    for link in soup.find_all("a", href=True):
        href = link["href"]
        
        # Check if it's a PDF link
        if href.lower().endswith(".pdf"):
            pdf_url = urljoin(base_url, href)  # Ensure absolute URL
            
            # Extract year and quarter from link text or href
            link_text = link.get_text(strip=True)
            pdf_name = href.split("/")[-1]  # Extract file name
            
            # Debugging output for each PDF link found
            print(f"Found PDF: {pdf_url}")
            print(f"Link text: {link_text}")
            print(f"PDF name: {pdf_name}")
            
            # Match only the required quarters and years
            if any(year in link_text or year in pdf_name for year in YEARS) and \
               any(qtr in link_text or qtr in pdf_name for qtr in QUARTERS):
                print(f"Match found for PDF: {pdf_url}")
                download_parse_upload_pdf(pdf_url, bucket_name, pdf_name)

def download_parse_upload_pdf(pdf_url, bucket_name, pdf_name):
    """Download a PDF file, parse it using Docling, and upload the parsed content to S3."""
    try:
        print(f"Attempting to download PDF: {pdf_url}")
        response = requests.get(pdf_url, stream=True)
        if response.status_code == 200:
            pdf_buffer = io.BytesIO(response.content)
            
            # Parse PDF with Docling
            extractor = Extractor()
            parsed_content = extractor.parse(pdf_buffer)
            
            # Convert parsed content to text format
            parsed_text = parsed_content.to_json()
            
            # Define S3 file path for raw PDF and parsed text
            s3_pdf_path = f"nvidia_financials/{pdf_name}"
            s3_text_path = f"nvidia_financials/parsed/{pdf_name.replace('.pdf', '.json')}"
            
            # Upload raw PDF
            print(f"Uploading {pdf_name} to S3: {s3_pdf_path}")
            s3_hook = S3Hook(aws_conn_id="aws_default")
            s3_hook.get_conn().upload_fileobj(pdf_buffer, bucket_name, s3_pdf_path)
            
            # Upload parsed text
            print(f"Uploading parsed text to S3: {s3_text_path}")
            s3_hook.get_conn().put_object(Bucket=bucket_name, Key=s3_text_path, Body=parsed_text)
            
            print(f"Uploaded {pdf_name} and parsed content to S3")

        else:
            print(f"Failed to download PDF: {pdf_url} (Status: {response.status_code})")
    
    except Exception as e:
        print(f"Error processing {pdf_url}: {e}")

# Run the scraper
scrape_nvidia_pdfs(BASE_URL, BUCKET_NAME)
