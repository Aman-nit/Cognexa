import os

from pathlib import Path

from dotenv import load_dotenv

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "cognexa-rag"
)

# Set project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Load TXT files
loader = DirectoryLoader(
    str(DATA_DIR),
    glob="*.txt",
    loader_cls=TextLoader
)

documents = loader.load()

print(f"Documents loaded: {len(documents)}")

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = text_splitter.split_documents(documents)

print(f"Total chunks created: {len(chunks)}")

# Connect to Pinecone
pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(INDEX_NAME)

# Prepare records
records = []

for i, chunk in enumerate(chunks):
    records.append({
        "_id": f"chunk-{i}",
        "text": chunk.page_content,
        "source": chunk.metadata.get("source", "")
    })

# Upload records to Pinecone
index.upsert_records(
    namespace="cognexa",
    records=records
)

print("Ingestion completed successfully!")
print(f"Total chunks uploaded: {len(records)}")
print(f"Index: {INDEX_NAME}")