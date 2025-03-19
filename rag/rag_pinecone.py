import pinecone
import numpy as np
from sentence_transformers import SentenceTransformer
from chunking import recursive_character_split

# Initialize Pinecone
pinecone.init(api_key="your-pinecone-api-key", environment="us-west1-gcp")
index = pinecone.Index("nvidia-reports")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_embedding(text):
    """Compute embedding for a given text."""
    return model.encode(text).tolist()

def store_in_pinecone(documents, quarters):
    """Store document chunks in Pinecone with metadata."""
    for i, doc in enumerate(documents):
        chunks = recursive_character_split(doc)
        for j, chunk in enumerate(chunks):
            doc_id = f"{i}-{j}"
            index.upsert([(doc_id, compute_embedding(chunk), {"quarter": quarters[i]})])

def query_pinecone(query, quarter_filter=None):
    """Retrieve relevant documents from Pinecone, with optional quarter filtering."""
    query_embedding = compute_embedding(query)
    results = index.query(query_embedding, top_k=5, include_metadata=True)
    
    # Apply quarter filter if specified
    if quarter_filter:
        results = [match for match in results["matches"] if match["metadata"]["quarter"] == quarter_filter]

    return results
