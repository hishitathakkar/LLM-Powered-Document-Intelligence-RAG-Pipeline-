import nltk
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

# Download NLTK models
nltk.download("punkt")

# 1️⃣ Recursive Character Text Splitter (LangChain)
def recursive_character_split(text, chunk_size=256, chunk_overlap=50):
    """
    Splits text using RecursiveCharacterTextSplitter from LangChain.
    Preserves meaning using smart boundary logic.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return text_splitter.split_text(text)

# 2️⃣ Token-based Chunking using TikToken (OpenAI tokenizer)
def token_text_split(text, chunk_size=256):
    """
    Splits text based on token count using TikToken.
    """
    encoding = tiktoken.get_encoding("cl100k_base")  # Suitable for OpenAI-compatible models
    tokens = encoding.encode(text)

    chunks = []
    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i:i + chunk_size]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

    return chunks

# 3️⃣ Semantic Sentence Splitter using NLTK
def semantic_split(text):
    """
    Splits text into sentences using NLTK's Punkt tokenizer.
    """
    return nltk.tokenize.sent_tokenize(text)
