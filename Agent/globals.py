import os
from dotenv import load_dotenv
load_dotenv()

class Config:

    # Agent
    agent_name = os.getenv("AGENT_NAME", "Copa")
    env = os.getenv("ENV", "dev")
    model = os.getenv("CHAT_MODEL")
    prompt_path = os.getenv("PROMPT_PATH")

    # Testing
    group = os.getenv("GROUP", "9")

    # RAG
    embedding_model  = os.getenv("EMBEDDING_MODEL")
    vector_store_api_key = os.getenv(f"PINECONE_API_KEY")
    namespace = os.getenv("PINECONE_NAMESPACE")
    index_name = os.getenv("PINECONE_INDEX")

    # API call error handling
    backoff_factor = float(os.getenv("BACKOFF_FACTOR", 0.5))
    max_retries = int(os.getenv("MAX_RETRIES", 3))

    # GUI/Gradio
    hf_token = os.getenv("HF_TOKEN")