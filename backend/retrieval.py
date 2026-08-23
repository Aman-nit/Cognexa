import os

from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "cognexa-rag")

# Connect to Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# Retrieve relevant context
def retrieve_documents(query, k=3):

    results = index.search(
        namespace="cognexa",
        query={
            "inputs": {
                "text": query
            },
            "top_k": k
        },
        fields=["text", "source"]
    )

    context = []

    for result in results["result"]["hits"]:

        text = result["fields"].get("text")

        if text:
            context.append(text)

    return "\n\n".join(context)