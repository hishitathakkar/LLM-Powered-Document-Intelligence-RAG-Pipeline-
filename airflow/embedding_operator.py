def embed_chunks(method, **kwargs):
    chunks = kwargs['ti'].xcom_pull(key='chunks')
    print(f"Embedding using: {method}")
    
    if method == 'manual':
        embeddings = [f"embedding({chunk})" for chunk in chunks]
    elif method == 'pinecone':
        embeddings = [f"pinecone_vec({chunk})" for chunk in chunks]
    elif method == 'chromadb':
        embeddings = [f"chromadb_vec({chunk})" for chunk in chunks]
    else:
        raise ValueError("Unknown embedding method")
    
    kwargs['ti'].xcom_push(key='embeddings', value=embeddings)
