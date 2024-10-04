
from RAG import RAG
from dotenv import load_dotenv
from globals import Config
import openai
import logging
import time

load_dotenv()

logging.basicConfig(level=logging.INFO)

class Agent:
    """
    A collaborative "knowledgeable peer" agent that interacts with users using RAG (Retrieval Augmented Generation)
    and OpenAI's chat completions API.

    The Agent class is responsible for:
    - Managing conversation flow.
    - Loading system prompts, task contexts, and student models based on the environment.
    - Retrieving domain knowledge using a RAG instance and augmenting user queries.
    - Communicating with OpenAI's API to generate conversational responses.

    Attributes
    ----------
    RAG : RAG
        An instance of the RAG class for handling retrieval-augmented generation for domain knowledge.
    has_spoken : bool
        A flag indicating whether the agent has already spoken in the current conversation.
    messages : list
        A list of dictionaries representing the conversation history.
    student_model : str, optional
        The student's computational model, loaded from a file, used in "dev" mode for testing.
    task_context : str, optional
        The student's task context, loaded from a file, used in "dev" mode for testing.
    """
    def __init__(self):
        self.RAG = RAG() 
        self.has_spoken = False
        self.messages = [{"role": "system", "content": self._load_file(Config.prompt_path)}]

        if Config.env == "dev":
            self.student_model = self._load_file(f'test/g{Config.group}/test_student_model.txt')
            self.task_context = self._load_file(f'test/g{Config.group}/test_task_context.txt')
        else:
            # This will be dynamic in production, but right now will have same values as in dev
            self.student_model = self._load_file(f'test/g{Config.group}/test_student_model.txt')
            self.task_context = self._load_file(f'test/g{Config.group}/test_task_context.txt')

    def _load_file(self, file_path):
        """
        Helper function to load file content into a string.

        Parameters
        ----------
        file_path : str
            The path to the file to load.

        Returns
        -------
        str
            Contents of the file or an empty string if the file is not found.
        """
        try:
            with open(file_path, 'r') as f:
                logging.info(f"Successfully loaded file from Agent class: '{file_path}'")
                return f.read()
        except (FileNotFoundError, IOError) as e:
            logging.error(f"Error loading file from Agent class: '{file_path}': {e}")
            return ""

    def _get_openai_response(self, messages, temperature=0.0):
        """
        Calls the OpenAI API to generate a response based on the provided conversation history.

        This method sends a list of conversation messages to the OpenAI chat completions API
        and retrieves the assistant's response. If the API call fails due to rate limits, 
        connection issues, or other errors, it retries the request up to `Config.max_retries` 
        times, with an exponential backoff between retries.

        Parameters
        ----------
        messages : list of dict
            A list of dictionaries representing the conversation history, with each dictionary 
            containing the role (e.g., "system", "user", "assistant") and the content of the message.

        Returns
        -------
        str
            The assistant's response message if the API call is successful, or an error message if 
            the API fails after all retries.

        Raises
        ------
        openai.RateLimitError
            Raised when the OpenAI API's rate limit is exceeded. The function will retry after an 
            exponential backoff.
        openai.APIConnectionError
            Raised when there is a connection issue with the OpenAI API. The function will retry 
            after an exponential backoff.
        openai.APIError
            Raised for other general API errors. The function will retry after an exponential backoff.

        Notes
        -----
        - The retry mechanism is controlled by `Config.max_retries`, which specifies the maximum number of retry attempts.
        - The exponential backoff mechanism waits for `Config.backoff_factor * (2 ** i)` seconds before retrying, where `i` 
        is the current retry attempt.
        - If the retries are exhausted, a default error message is returned: 
        "I'm sorry, I don't think I'm understanding you correctly. Can you explain?"
        """
        for i in range(Config.max_retries):
            try:
                response = openai.chat.completions.create(
                    model=Config.model,
                    temperature=temperature,
                    messages=messages
                )
                logging.info(f"Successfully called OpenAI API in Agent class.'")
                return response.choices[0].message.content
            except openai.RateLimitError:
                logging.error(f"Open AI Rate limit exceeded for response call from Agent, retry {i+1}/{Config.max_retries}.")
                time.sleep(Config.backoff_factor * (2 ** i))
            except openai.APIConnectionError as e:
                logging.error(f"OpenAI API connection error for response call from Agent: {e}, retry {i+1}/{Config.max_retries}")
                time.sleep(Config.backoff_factor * (2 ** i))
            except openai.APIError as e:
                logging.error(f"OpenAI API error for response call from Agent: {e}, retry {i+1}/{Config.max_retries}")
                time.sleep(Config.backoff_factor * (2 ** i))
        return "I'm sorry, I don't think I'm understanding you correctly. Can you explain?"
        
    def print_messages(self):
        """
        Prints the entire message history of the conversation.
        """
        for m in self.messages:
            print("------------------------------------------------------------------------")
            print("ROLE:", m["role"])
            print("CONTENT:", m["content"])

    def _process_query(self, user_query):
        """
        Processes user input and updates conversation messages.

        Parameters
        ----------
        user_query : str
            The input from the user.

        Returns
        -------
        None
        """
        if not self.has_spoken:
            # First query: Perform RAG retrieval
            q_embed = self.RAG.get_embeddings([user_query])[0]
            matches = self.RAG.retrieve(q_embed, 3)["matches"]
            domain_context = "\n\n".join([m["metadata"]["text"] for m in matches])
            self.messages[0]["content"] += f"\n\nDomain Context:\n{domain_context}"
    
            # Create the initial user message including task context and student model
            user_message_str = f"Task Context:\n{self.task_context}\n\nStudent Query:\n{user_query}\n\nStudent Computational Model:\n{self.student_model}"
        else:
            # Subsequent queries: only include the user query/response in the messages
            user_message_str = user_query
        
        self.messages.append({"role": "user", "content": user_message_str})

        # Get and print assistant response
        response_text = self._get_openai_response(self.messages)
        print(f"\n{Config.agent_name}: {response_text}\n")
        self.messages.append({"role": "assistant", "content": response_text})

        # Set flag to indicate that the agent has spoken
        if not self.has_spoken:
            self.has_spoken = True

    def talk(self):
        """
        Starts an interactive conversation with the user and continues until a termination command is given.
        """
        intro_str = f"Hi, I'm {Config.agent_name}, a collaborative peer agent! Is there something I can help you with?"
        intro_str_rephrase = self._get_openai_response(
            messages=
                [
                    {"role": "system", "content": "Rephrase this introduction:\n"},
                    {"role": "user", "content": intro_str}
                ],
            temperature=0.5
        )

        stop_words = {"q", "quit", "stop", "end"}
        
        user_query = input(f"\n{Config.agent_name}: "+intro_str_rephrase+"\n\n"+"Student: ").lower()

        if user_query in stop_words:
            self.end_conversation()
            return

        # Process the first query
        self._process_query(user_query)

        # Loop to process further queries
        while (new_query := input("Student: ").lower()) not in stop_words:
            self._process_query(new_query)

        self.end_conversation()

    def end_conversation(self):
        """
        Terminates the conversation.
        """
        # Optionally print messages in 'dev' environment once conversation ends
        if Config.env == "dev":
            self.print_messages()