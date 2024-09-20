from pinecone import Pinecone
import openai
import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY = os.getenv(f"PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)

KB_PATH = os.getenv("KB_PATH")
with open(KB_PATH) as f:
    data_string = "".join([line for line in f])

data_arr = data_string.split("\n\n")

data_labels = ["displacement","velocity","acceleration","time","final_velocity_eq","displacement_eq",\
               "velocity_squared_eq","updating_velocity_eq","updating_position_eq","variable","constant",\
                "init_variable","update_variable","loops","conditionals"]

assert len(data_arr)==len(data_labels)==15

data = [{"id":data_labels[i], "text":data_arr[i]} for i in range(len(data_labels))]

def embed(docs: list[str]) -> list[list[float]]:
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    res = openai.embeddings.create(
        input=docs,
        model=EMBEDDING_MODEL
    )
    doc_embeds = [r.embedding for r in res.data]
    return doc_embeds

text_to_embed = [d["text"] for d in data]
embeddings = embed(docs=text_to_embed)

INDEX_NAME = os.getenv("PINECONE_INDEX")
index = pc.Index(INDEX_NAME)

vectors = []
for d, e in zip(data, embeddings):
    vectors.append({
        "id": d['id'],
        "values": e,
        "metadata": {'text': d['text']}
    })

PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE")
index.upsert(
    vectors=vectors,
    namespace=PINECONE_NAMESPACE
)

# print(index.describe_index_stats())