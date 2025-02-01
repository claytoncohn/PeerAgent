import os
from dotenv import load_dotenv
load_dotenv()

class Config:

    # Agent
    agent_name = os.getenv("AGENT_NAME", "Copa")
    env = os.getenv("ENV", "dev")
    model = os.getenv("CHAT_MODEL")
    prompt_path = os.getenv("PROMPT_PATH")
    rag_summary_prompt_path = os.getenv("RAG_SUMMARY_PROMPT_PATH")
    summary_few_shot_instances_path = os.getenv("SUMMARY_FEW_SHOT_INSTANCES_PATH")
    convo_save_path = os.getenv("CONVO_SAVE_PATH")
    word_threshold = int(os.getenv("MODEL_WORD_THRESHOLD"))

    # Testing
    group = os.getenv("GROUP")

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