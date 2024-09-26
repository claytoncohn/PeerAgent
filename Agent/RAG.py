from pinecone import Pinecone
import openai
import os
from dotenv import load_dotenv
load_dotenv()

class RAG:
    def __init__(self):
        self.embedding_model  = os.getenv("EMBEDDING_MODEL")
        self.vector_store = Pinecone(api_key=os.getenv(f"PINECONE_API_KEY"))
        self.namespace = os.getenv("PINECONE_NAMESPACE")
        self.index_name = os.getenv("PINECONE_INDEX")

    def get_embeddings(self,e):
        res = openai.embeddings.create(
            input=[e],
            model=self.embedding_model
        )
        doc_embeds = [r.embedding for r in res.data]
        return doc_embeds 
    
    def retrieve(self,embedding,k):
        index = self.vector_store.Index(self.index_name)
        result = index.query(
            namespace=self.namespace,
            vector=embedding,
            top_k=k,
            include_values=False,
            include_metadata=True
        )
        return result