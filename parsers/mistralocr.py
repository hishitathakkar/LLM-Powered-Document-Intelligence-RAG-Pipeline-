import json
import base64
import requests
from pathlib import Path
from mistralai import Mistral, DocumentURLChunk
from mistralai.models import OCRResponse
from dotenv import load_dotenv
import os
from chunking import recursive_character_split, token_text_split, semantic_split
from rag_naive import naive_rag_search
from rag_pinecone import store_in_pinecone
from rag_chroma import store_in_chroma

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("Mistral_API_KEY")
client = Mistral(api_key=api_key)

# Path configuration
PDF_URL = "1cbe8fe7-e08a-46e3-8dcc-b429fc06c1a4.pdf"  # Or use full URL
DONE_DIR = Path("pdfs-done")
OUTPUT_ROOT_DIR = Path("ocr_output")

# Ensure directories exist
DONE_DIR.mkdir(exist_ok=True)
OUTPUT_ROOT_DIR.mkdir(exist_ok=True)

def replace_images_in_markdown(markdown_str: str, images_dict: dict, pdf_base: str) -> str:
    for img_name, base64_str in images_dict.items():
        markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![](ocr_output/{pdf_base}/images/{img_name})")
    return markdown_str

def get_combined_markdown(ocr_response: OCRResponse, pdf_base: str) -> str:
    markdowns: list[str] = []
    for page in ocr_response.pages:
        image_data = {}
        for img in page.images:
            image_data[img.id] = img.image_base64
        markdowns.append(replace_images_in_markdown(page.markdown, image_data, pdf_base))
    return "\n\n".join(markdowns)

def process_pdf(pdf_url: str, rag_method="pinecone", chunking_strategy="recursive"):
    pdf_base = "extracted_pdf"
    print(f"Processing {pdf_url} ...")

    output_dir = OUTPUT_ROOT_DIR / pdf_base
    output_dir.mkdir(exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    ocr_response = client.ocr.process(
        document=DocumentURLChunk(document_url=pdf_url),
        model="mistral-ocr-latest",
        include_image_base64=True
    )

    # Save OCR in JSON
    ocr_json_path = output_dir / "ocr_response.json"
    with open(ocr_json_path, "w", encoding="utf-8") as json_file:
        json.dump(ocr_response.dict(), json_file, indent=4, ensure_ascii=False)
    print(f"OCR response saved in {ocr_json_path}")

    # OCR -> Markdown
    global_counter = 1
    updated_markdown_pages = []

    for page in ocr_response.pages:
        updated_markdown = page.markdown
        for image_obj in page.images:
            base64_str = image_obj.image_base64
            if base64_str.startswith("data:"):
                base64_str = base64_str.split(",", 1)[1]
            image_bytes = base64.b64decode(base64_str)

            ext = Path(image_obj.id).suffix if Path(image_obj.id).suffix else ".jpeg"
            new_image_name = f"{pdf_base}_img_{global_counter}{ext}"
            global_counter += 1

            image_output_path = images_dir / new_image_name
            with open(image_output_path, "wb") as f:
                f.write(image_bytes)

            updated_markdown = updated_markdown.replace(
                f"![{image_obj.id}]({image_obj.id})",
                f"![](ocr_output/{pdf_base}/images/{new_image_name})"
            )
        updated_markdown_pages.append(updated_markdown)

    final_markdown = "\n\n".join(updated_markdown_pages)
    output_markdown_path = output_dir / "output.md"
    with open(output_markdown_path, "w", encoding="utf-8") as md_file:
        md_file.write(final_markdown)
    print(f"Markdown generated in {output_markdown_path}")

    # 🔗 Connect to Chunking + RAG
    documents = [final_markdown]
    quarters = ["mistral-auto"]

    if rag_method == "pinecone":
        store_in_pinecone(documents, quarters, chunking_strategy)
    elif rag_method == "chroma":
        store_in_chroma(documents, quarters, chunking_strategy)
    elif rag_method == "naive":
        print("ℹ️ Naive RAG is used at query-time only.")
    else:
        print("⚠️ Invalid RAG method specified.")

# Run the PDF processing function
process_pdf(PDF_URL, rag_method="chroma", chunking_strategy="semantic")
