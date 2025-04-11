import chromadb
from sentence_transformers import SentenceTransformer
from chunking import recursive_character_split

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="nvidia_reports")

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

def compute_embedding(text):
    """Compute embedding for a document."""
    return model.encode(text).tolist()

def store_in_chroma(documents, quarters):
    """Store documents in ChromaDB with quarter metadata."""
    for i, doc in enumerate(documents):
        chunks = recursive_character_split(doc)
        for j, chunk in enumerate(chunks):
            doc_id = f"{i}-{j}"
            collection.insert({
                "id": doc_id,
                "text": chunk,
                "quarter": quarters[i],
                "embedding": compute_embedding(chunk)
            })

def query_chroma(query, quarter_filter=None):
    """Retrieve relevant documents from ChromaDB, with optional quarter filtering."""
    query_embedding = compute_embedding(query)
    results = collection.search(query_embedding, n_results=5)
    
    # Apply quarter filter
    if quarter_filter:
        results = [res for res in results if res["quarter"] == quarter_filter]

    return results