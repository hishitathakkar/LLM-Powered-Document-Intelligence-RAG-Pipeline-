from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import os
from io import BytesIO
from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from redis import Redis
from litellm import completion
from dotenv import load_dotenv
from redis_streams import redis_files
from chunking import recursive_character_split, token_text_split, semantic_split
from rag_chroma import store_in_chroma
from rag_pinecone import store_in_pinecone
from rag_naive import naive_rag_search
from rag_chroma import query_chroma
from rag_pinecone import query_pinecone
from rag_naive import naive_rag_search
from dockling import scrape_nvidia_pdfs
from mistralocr import process_pdf



app = FastAPI()

# Initialize Redis connection
redis_client = Redis(host='localhost', port=6379, db=0)

load_dotenv(r'Add\Path\to\environment\access.env')


# Set API key directly
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')


@app.post("/upload_pdf")
async def pdf_upload(file: UploadFile = File(...)):

    # Define size limit (3MB in bytes)
    MAX_FILE_SIZE = 3 * 1024 * 1024

    pdf_name = file.filename

    if not pdf_name.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")


    try:
        # Read the uploaded file's content
        file_content = await file.read()

        #pdf_name = file.filename
        #file_name = os.path.splitext(pdf_name)[0]

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 3MB limit")

        # Delete any existing cached file
        redis_client.delete("pdf_content", "markdown_content", "chunked_content", "pdf_method")

        # Save PDF to Redis cache
        redis_client.set("pdf_content", file_content)
        #redis_client.mset(new_dict)


        #file_url = process_pdf_s3_upload(parsed_content, file.filename)
        return {"message": "File uploaded successfully and cached in Redis stream"}
    

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    


@app.get("/pdf_parser")
async def pdf_parser(selected_parser: str):

    try:
        file = redis_files()
        # Add the call to Docling and Mistral Code here
        redis_client.delete("markdown_content", "chunked_content")

        # Convert bytes to string if file is PDF
        if isinstance(file, bytes):
            file = file.decode("utf-8")

        if selected_parser.lower() == "docling":
            # Call Docling + scraping + RAG logic
            scrape_nvidia_pdfs(rag_method="chroma", chunking_strategy="recursive")
            redis_client.set("markdown_content", "Docling scraping and processing completed.")

        elif selected_parser.lower() == "mistral ocr":
            # This example uses a static PDF URL in mistralocr.py
            process_pdf(
                pdf_url="https://example.com/your-uploaded.pdf", #Doubt
                rag_method="chroma",
                chunking_strategy="semantic"
            )
            redis_client.set("markdown_content", "Mistral OCR parsing and processing completed.")
        else:
            raise HTTPException(status_code=400, detail="Invalid parser selected.")

        return {"message": f"{selected_parser} parsing completed and content cached in Redis."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")


@app.get("/chunking_strat")
async def chunking_strat(selected_chunk: str):

    try:
        file = redis_files()
        # Add the call to Chunking Strategies Code here
        # Apply appropriate chunking strategy
        if selected_chunk.strip().lower().startswith("token"):
            chunks = token_text_split(file)
        elif selected_chunk.strip().lower().startswith("recursive"):
            chunks = recursive_character_split(file)
        elif selected_chunk.strip().lower().startswith("semantic"):
            chunks = semantic_split(file)
        else:
            raise ValueError("Invalid chunking strategy selected.")

        # Convert list to string for caching
        chunked_content = "\n".join(chunks)

        redis_client.delete("pdf_content", "markdown_content", "chunked_content")
        redis_client.set("chunked_content", chunked_content)

        return {"message": "Chunking completed and stored in Redis."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")



@app.get("/rag_method")
async def rag_method(selected_rag: str):

    try:
        file = redis_files()
        # Add the call to RAG Methods Code here
        # For demo, just use current quarter; replace with actual metadata as needed
        documents = [file]
        quarters = ["Q1"]

        if selected_rag.lower().startswith("pinecone"):
            store_in_pinecone(documents, quarters, chunking_strategy="recursive")
        elif selected_rag.lower().startswith("chroma"):
            store_in_chroma(documents, quarters, chunking_strategy="recursive")
        elif selected_rag.lower().startswith("manual"):
            pass  # Manual embedding may be a placeholder for naive RAG
        else:
            raise ValueError("Invalid RAG method selected.")

        return {"message": f"{selected_rag} RAG method successfully executed."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")




@app.get("/ask_question")
async def ask_question(question: str, selected_year: str, selected_quarter: str):

    try:

        # Call the context from RAG here
        quarter_filter = selected_quarter[0] if selected_quarter else None

        # Default to Chroma RAG
        result_chunks, _ = query_chroma(query=question, quarter_filter=quarter_filter)

        # Fall back to Naive RAG (for "Manual Embeddings" option)
        if not result_chunks:
            context, _, _ = naive_rag_search(question, [redis_client.get("chunked_content").decode()], chunking_strategy="recursive")
        else:
            context = "\n".join([doc["text"] for doc in result_chunks])


        messages = [
            {"role": "assistant", "content": context},
            {"role": "user", "content": f'{question}. Give your response based solely on the context provided. Do not make up information.'}
        ]

        # Use LiteLLM to answer the question
        response = completion(model='GPT-4o', messages=messages) 

        # Convert the response to a JSON-serializable format
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