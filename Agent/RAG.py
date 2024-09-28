from pinecone import Pinecone
import openai
from globals import Config
from dotenv import load_dotenv
import logging
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)

class RAG:
    """
    A class to implement Retrieval-Augmented Generation (RAG) using OpenAI's embeddings and Pinecone for vector storage.

    The class is designed to generate embeddings for input texts using OpenAI's API and retrieve the most relevant
    documents from Pinecone's vector store based on those embeddings.
    """
    def __init__(self):
        """
        Initializes the RAG class with configurations for OpenAI's embedding model and Pinecone vector store.

        Attributes
        ----------
        embedding_model : str
            The name of the OpenAI embedding model to be used for generating embeddings.
        vector_store : Pinecone
            The Pinecone client initialized with the API key from configuration.
        namespace : str
            The namespace in the Pinecone vector store where the index is located.
        index_name : str
            The name of the index in Pinecone to query.
        index : Pinecone.Index
            The Pinecone index object to perform retrieval operations.
        """
        self.embedding_model  = Config.embedding_model
        self.vector_store = Pinecone(api_key=Config.vector_store_api_key)
        self.namespace = Config.namespace
        self.index_name = Config.index_name
        self.index = self.vector_store.Index(self.index_name)

    def get_embeddings(self,texts):
        """
        Generate embeddings for a list of input texts using the OpenAI API.

        This method makes an API call to OpenAI's embeddings endpoint and retrieves the vector representation
        (embeddings) for each input text. If rate limits or errors occur, it retries with exponential backoff.

        Parameters
        ----------
        texts : list of str
            A list of texts for which embeddings need to be generated.
        retries : int, optional
            The number of retry attempts in case of an API error or rate limit, by default 3.
        backoff_factor : float, optional
            The factor by which the retry wait time increases exponentially after each retry, by default 0.5 seconds.

        Returns
        -------
        list of list of float or None
            A list of embeddings for the input texts, or None if the API call fails after all retries.

        Raises
        ------
        openai.RateLimitError
            Raised when the OpenAI API's rate limit is exceeded.
        openai.APIConnectionError
            Raised when there is a connection issue with the OpenAI API.
        openai.APIError
            Raised when a generic error occurs while calling the OpenAI API.
        """
        for i in range(Config.max_retries):
            try: 
                res = openai.embeddings.create(
                    input=texts,
                    model=self.embedding_model
                )
                logging.info(f"Successfully retrieved embeddings from OpenAI embedding model in RAG class.'")
                doc_embeds = [r.embedding for r in res.data]
                return doc_embeds 
            except openai.RateLimitError:
                logging.error(f"Open AI Rate limit exceeded for embedding call from RAG, retry {i+1}/{Config.max_retries}.")
                time.sleep(Config.backoff_factor * (2 ** i))
            except openai.APIConnectionError as e:
                logging.error(f"OpenAI API connection error for embedding call from RAG: {e}, retry {i+1}/{Config.max_retries}")
                time.sleep(Config.backoff_factor * (2 ** i))
            except openai.APIError as e:
                logging.error(f"OpenAI API error for embedding call from RAG: {e}, retry {i+1}/{Config.max_retries}")
                time.sleep(Config.backoff_factor * (2 ** i))
        return None
    
    def retrieve(self,embedding,k):
        """
        Retrieve the top-k most relevant documents from the Pinecone vector store based on an input embedding.

        This method performs a query to the Pinecone index, returning metadata for the top-k documents
        most similar to the input embedding. If the query fails due to API errors, it retries with exponential backoff.

        Parameters
        ----------
        embedding : list of float
            The embedding vector for which to retrieve the most similar documents from Pinecone.
        k : int
            The number of top documents to retrieve based on similarity to the input embedding.
        retries : int, optional
            The number of retry attempts in case of a query error, by default 3.
        backoff_factor : float, optional
            The factor by which the retry wait time increases exponentially after each retry, by default 0.5 seconds.

        Returns
        -------
        dict or None
            A dictionary containing metadata and results from the Pinecone index query, or None if the query fails after all retries.

        Raises
        ------
        Exception
            Raised if an unknown error occurs while querying the Pinecone index.
        """
        for i in range(Config.max_retries):
            try:
                result = self.index.query(
                    namespace=self.namespace,
                    vector=embedding,
                    top_k=k,
                    include_values=False,
                    include_metadata=True
                )
                logging.info(f"Successfully retrieved domain knowledge from vector store in RAG class.'")
                return result
            except Exception as e:
                logging.error(f"Pinecone API error for retrieving from knowledge base in RAG class: {e}, retry {i+1}/{Config.max_retries}")
                time.sleep(Config.backoff_factor * (2 ** i))
        return None