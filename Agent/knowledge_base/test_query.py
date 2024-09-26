from pinecone import Pinecone
from upsert_data import embed
import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY = os.getenv(f"PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)

# Good
# queries = ["What is velocity?", "I forgot the kinematic equations.", "What is the relationship between acceleration and velocity?"]

# Bad
queries = ["truck won't move?", "why is it moving backwards?", "it's not slowing down", "my dog is my best friend!"]

embeddings = embed(queries)

def get_query_result(embedding):
    NAMESPACE = os.getenv("PINECONE_NAMESPACE")
    INDEX_NAME = os.getenv("PINECONE_INDEX")
    index = pc.Index(INDEX_NAME)
    result = index.query(
        namespace=NAMESPACE,
        vector=embedding,
        top_k=3,
        include_values=False,
        include_metadata=True
    )
    return result

for q,e in zip(queries,embeddings):
    print("Query:",q)
    print(get_query_result(e),"\n\n")