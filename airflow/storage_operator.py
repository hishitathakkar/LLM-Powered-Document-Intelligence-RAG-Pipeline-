def store_embeddings(rag_method, **kwargs):
    embeddings = kwargs['ti'].xcom_pull(key='embeddings')
    print(f"Storing to RAG method: {rag_method}")
    
    # Mock storage operation
    for vec in embeddings:
        print(f"Storing vector: {vec}")
