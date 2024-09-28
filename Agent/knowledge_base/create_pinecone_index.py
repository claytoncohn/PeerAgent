from pinecone import Pinecone, ServerlessSpec
import os
from dotenv import load_dotenv
load_dotenv()

"""
Load environment variables and set up a Pinecone index using the Pinecone client and ServerlessSpec.

This script initializes a Pinecone client using an API key retrieved from environment variables, and creates a Pinecone index with specified parameters.

Modules:
    pinecone (Pinecone, ServerlessSpec): Used to interact with Pinecone for creating and managing vector indexes.
    os: Provides a way to interact with the operating system for environment variables.
    dotenv (load_dotenv): Loads environment variables from a `.env` file.

Attributes:
    PINECONE_API_KEY (str): The API key used to authenticate with Pinecone.
    pc (Pinecone): An instance of the Pinecone client.
    index_name (str): The name of the Pinecone index to be created, fetched from environment variables.
    dim_size (int): The number of dimensions in the vectors for the Pinecone index (default is 3072).

Functions:
    pc.create_index:
        Create a Pinecone index with the specified parameters.

    Parameters:
        name (str): Name of the index.
        dimension (int): The dimensionality of the vectors stored in the index.
        metric (str): The distance metric to be used for similarity searches (e.g., "cosine").
        spec (ServerlessSpec): The serverless specification for cloud and region settings.

Usage Example:
    Ensure the `.env` file contains `PINECONE_API_KEY` and `PINECONE_INDEX` variables before running the script. 
    This will initialize a Pinecone client and create an index with the specified dimensionality and settings.
"""

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