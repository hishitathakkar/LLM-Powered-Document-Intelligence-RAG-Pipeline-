from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import os
from io import BytesIO
from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from redis import Redis
from litellm import completion
from dotenv import load_dotenv
from redis_streams import redis_files

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





        # Delete any existing cached file
        redis_client.delete("pdf_content", "markdown_content", "chunked_content")

        # Save markdown file to Redis cache
        redis_client.set("markdown_content", markdown_content)



    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")
    


@app.get("/chunking_strat")
async def pdf_parser(selected_chunk: str):

    try:
        file = redis_files()
        # Add the call to Chunking Strategies Code here






        # Delete any existing cached file
        redis_client.delete("pdf_content", "markdown_content", "chunked_content")

        # Save PDF to Redis cache
        redis_client.set("chunked_content", chunked_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")
    


@app.get("/rag_method")
async def pdf_parser(selected_rag: str):

    try:
        file = redis_files()
        # Add the call to RAG Methods Code here


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning a response: {str(e)}")




@app.get("/ask_question")
async def ask_question(question: str, selected_year: str, selected_quarter: str):

    try:

        # Call the context from RAG here





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