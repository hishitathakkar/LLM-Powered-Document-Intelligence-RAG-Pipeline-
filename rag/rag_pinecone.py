import pinecone
import numpy as np
from sentence_transformers import SentenceTransformer
from chunking import recursive_character_split, token_text_split, semantic_split

# Initialize Pinecone
pinecone.init(api_key="your-pinecone-api-key", environment="us-east-1-aws")
index = pinecone.Index("nvidia-reports")

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_embedding(text):
    """Compute embedding for a given text."""
    return model.encode(text).tolist()

def apply_chunking_strategy(text, strategy):
    if strategy == "recursive":
        return recursive_character_split(text)
    elif strategy == "token":
        return token_text_split(text)
    elif strategy == "semantic":
        return semantic_split(text)
    else:
        raise ValueError("Invalid chunking strategy. Choose from: recursive, token, semantic")

def store_in_pinecone(documents, quarters, chunking_strategy="recursive"):
    """Store document chunks in Pinecone with metadata and chosen chunking strategy."""
    for i, doc in enumerate(documents):
        chunks = apply_chunking_strategy(doc, chunking_strategy)
        for j, chunk in enumerate(chunks):
            doc_id = f"{i}-{j}"
            index.upsert([
                {
                    "id": doc_id,
                    "values": compute_embedding(chunk),
                    "metadata": {"quarter": quarters[i]}
                }
            ])

def query_pinecone(query, quarter_filter=None):
    """Retrieve relevant documents from Pinecone, with optional quarter filtering."""
    query_embedding = compute_embedding(query)
    results = index.query(vector=query_embedding, top_k=5, include_metadata=True)

    matches = results["matches"]
    if quarter_filter:
        matches = [m for m in matches if m["metadata"].get("quarter") == quarter_filter]

    return matches
