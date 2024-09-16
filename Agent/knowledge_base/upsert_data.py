import pinecone as pc
import openai
import os
from dotenv import load_dotenv
load_dotenv()

KB_PATH = os.getenv("KB_PATH")
with open(KB_PATH) as f:
    data_string = "".join([line for line in f])

data_arr = data_string.split("\n\n")
print(data_arr)


# data = [

#     {"id": "vec1", "text": "Apple is a popular fruit known for its sweetness and crisp texture."},

#     {"id": "vec2", "text": "The tech company Apple is known for its innovative products like the iPhone."},

#     {"id": "vec3", "text": "Many people enjoy eating apples as a healthy snack."},

#     {"id": "vec4", "text": "Apple Inc. has revolutionized the tech industry with its sleek designs and user-friendly interfaces."},

#     {"id": "vec5", "text": "An apple a day keeps the doctor away, as the saying goes."},

#     {"id": "vec6", "text": "Apple Computer Company was founded on April 1, 1976, by Steve Jobs, Steve Wozniak, and Ronald Wayne as a partnership."}

# ]

# embeddings = pc.inference.embed(

#     model="multilingual-e5-large",

#     inputs=[d['text'] for d in data],

#     parameters={"input_type": "passage", "truncate": "END"}

# )

# EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
# def embed(docs: list[str]) -> list[list[float]]:
#     res = openai.embeddings.create(
#         input=docs,
#         model=EMBEDDING_MODEL
#     )
#     doc_embeds = [r.embedding for r in res.data]
#     return doc_embeds

# print(embeddings[0])