import os

class Config:

    # Agent
    agent_name = os.getenv("AGENT_NAME", "Copa")
    env = os.getenv("ENV", "dev")
    model = os.getenv("CHAT_MODEL", "gpt-4o")
    prompt_path = os.getenv("PROMPT_PATH")
    student = os.getenv("STUDENT", "1")

    # RAG
    embedding_model  = os.getenv("EMBEDDING_MODEL")
    vector_store_api_key = os.getenv(f"PINECONE_API_KEY")
    namespace = os.getenv("PINECONE_NAMESPACE")
    index_name = os.getenv("PINECONE_INDEX")

    # API call error handling
    backoff_factor = os.getenv("BACKOFF_FACTOR", 0.5)
    max_retries = os.getenv("MAX_RETRIES", 3)