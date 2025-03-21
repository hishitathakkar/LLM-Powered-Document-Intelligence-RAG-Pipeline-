import numpy as np
from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine
from chunking import recursive_character_split, token_text_split, semantic_split

# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_embedding(text):
    """Compute embeddings for a given text chunk."""
    return model.encode(text)

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return 1 - cosine(vec1, vec2)

def naive_rag_search(query, documents, chunking_strategy="recursive"):
    """
    Implements a naive RAG retrieval with different chunking strategies.
    """
    query_embedding = compute_embedding(query)
    
    # Choose chunking strategy
    chunked_docs = []
    for doc in documents:
        if chunking_strategy == "recursive":
            chunked_docs.extend(recursive_character_split(doc))
        elif chunking_strategy == "token":
            chunked_docs.extend(token_text_split(doc))
        elif chunking_strategy == "semantic":teamstea
            chunked_docs.extend(semantic_split(doc))
        else:
            raise ValueError("Invalid chunking strategy. Choose from: recursive, token, semantic")

    # Compute embeddings and retrieve best match
    doc_embeddings = [compute_embedding(doc) for doc in chunked_docs]
    similarities = [cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_embeddings]

    best_match_index = np.argmax(similarities)
    return chunked_docs[best_match_index], similarities[best_match_index]
