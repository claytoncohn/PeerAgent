from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY = os.getenv(f"PINECONE_API_KEY")

pc = Pinecone(api_key=PINECONE_API_KEY)

index_name = os.getenv("PINECONE_INDEX")
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