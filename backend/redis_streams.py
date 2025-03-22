from io import BytesIO
from fastapi.responses import JSONResponse
from redis import Redis

# Initialize Redis connection
redis_client = Redis(host='localhost', port=6379, db=0)

def redis_files():

    if redis_client.exists("pdf_content"):
        
        # Retrieve PDF file from Redis
        context = redis_client.get("pdf_content")   

    # Check if Markdown is cached
    elif redis_client.exists("markdown_content"):

        # Retrieve Markdown text from Redis
        markdown_text = redis_client.get("markdown_content")

        # Prepare context for LiteLLM
        context = markdown_text.decode("utf-8")

    # Check if Chunked Text is cached
    elif redis_client.exists("chunked_content"):

        # Retrieve Markdown text from Redis
        chunked_text = redis_client.get("chunked_content")

        # Prepare context for LiteLLM
        context = chunked_text.decode("utf-8")


    else:
        return JSONResponse(content={"error": "PDF or Markdown file not found"}, status_code=400)
    

    return context