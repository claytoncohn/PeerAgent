from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY = os.getenv(f"PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = "openai-text-embedding-3-large-4072"
dim_size = 3072

pc.create_index(
    name=index_name,
    dimension=dim_size,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)