import nltk
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

nltk.download("punkt")  # Ensure this is available in Docker container

def chunk_pdf(strategy, **kwargs):
    """
    Chunk the parsed text into smaller parts using selected strategy:
    - 'fixed': LangChain RecursiveCharacterTextSplitter
    - 'tokens': Token-based chunking with TikToken
    - 'semantic': Sentence-based chunking with NLTK
    """
    ti = kwargs['ti']
    parsed_text = ti.xcom_pull(key='parsed_text')

    if not parsed_text:
        raise ValueError("No parsed text found in XCom")

    if strategy == 'fixed':
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=256,
            chunk_overlap=50
        )
        chunks = text_splitter.split_text(parsed_text)

    elif strategy == 'tokens':
        encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(parsed_text)

        chunks = []
        for i in range(0, len(tokens), 256):
            chunk_tokens = tokens[i:i + 256]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

    elif strategy == 'semantic':
        chunks = nltk.tokenize.sent_tokenize(parsed_text)

    else:
        raise ValueError(f"Unsupported chunking strategy: {strategy}")

    print(f"Chunked text into {len(chunks)} parts using strategy: {strategy}")
    ti.xcom_push(key='chunks', value=chunks)
