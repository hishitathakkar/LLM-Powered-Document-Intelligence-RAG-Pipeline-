import chromadb
from sentence_transformers import SentenceTransformer
from chunking import recursive_character_split, token_text_split, semantic_split

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="nvidia_reports")

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_embedding(text):
    """Compute embedding for a document."""
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

def store_in_chroma(documents, quarters, chunking_strategy="recursive"):
    """Store documents in ChromaDB with chunking strategy."""
    for i, doc in enumerate(documents):
        chunks = apply_chunking_strategy(doc, chunking_strategy)
        for j, chunk in enumerate(chunks):
            doc_id = f"{i}-{j}"
            collection.insert(
                ids=[doc_id],
                documents=[chunk],
                metadatas=[{"quarter": quarters[i]}],
                embeddings=[compute_embedding(chunk)]
            )

def query_chroma(query, quarter_filter=None):
    """Retrieve relevant documents from ChromaDB, with optional quarter filtering."""
    query_embedding = compute_embedding(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=5, include=["metadatas", "documents"])

    # Flatten and filter
    results_list = []
    for doc, metadata in zip(results['documents'][0], results['metadatas'][0]):
        if not quarter_filter or metadata.get("quarter") == quarter_filter:
            results_list.append({"text": doc, "quarter": metadata.get("quarter")})

    return results_list
