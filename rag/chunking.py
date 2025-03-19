import nltk
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
import tiktoken

nltk.download("punkt")

# 1️⃣ Recursive Character Text Splitter
def recursive_character_split(text, chunk_size=256, chunk_overlap=50):
    """Uses RecursiveCharacterTextSplitter to split text while preserving meaning."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

# 2️⃣ Token Text Splitter (Token-based chunking)
def token_text_split(text, chunk_size=256):
    """Uses TokenTextSplitter to split text based on token count."""
    encoding = tiktoken.get_encoding("cl100k_base")  # OpenAI GPT encoding
    tokens = encoding.encode(text)
    
    chunks = []
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i : i + chunk_size]
        chunks.append(encoding.decode(chunk_tokens))
    
    return chunks

# 3️⃣ Semantic Text Splitter (Sentence-based)
def semantic_split(text):
    """Splits text into meaningful sentences."""
    return nltk.tokenize.sent_tokenize(text)
