from learner_model import LearnerModel
from rag import RAG
import os
from globals import Config
import openai
import logging
import datetime
import pytz
import time
import gradio as gr
import json
import time
from dotenv import load_dotenv
load_dotenv()

epoch_time = str(time.time()).split(".")[0]

logging.info("Successfully imported Agent class libraries.")
logging.basicConfig(level=logging.INFO)

class Agent:
    """
    A collaborative "knowledgeable peer" agent that interacts with users using Retrieval-Augmented Generation (RAG) 
    and OpenAI's chat completions API.

    The `Agent` class is responsible for managing the conversation flow, retrieving relevant domain knowledge, 
    augmenting user queries with context, and generating responses using OpenAI's API. It facilitates interaction 
    between users and a knowledge-based assistant designed to support learning and problem-solving.

    Attributes
    ----------
    use_gui : bool
        A flag indicating whether the agent should use a graphical user interface (GUI) for interaction.
    RAG : RAG
        An instance of the `RAG` class responsible for retrieval-augmented generation, enabling domain knowledge retrieval.
    has_spoken : bool
        A flag indicating whether the agent has already spoken in the current conversation.
    messages : list of dict
        A list containing dictionaries representing the conversation history. Each message has a "role" (e.g., 
        "system", "user", "assistant") and a "content" field.
    learner_model : str
        Students' learner model, used for guiding agent interactions.
    running_word_count : int
        The total number of words in the conversation history, used for monitoring token usage.
    message_truncation_count : int
        The number of times messages have been truncated to stay within token limits.

    Methods
    -------
    __init__(use_gui=False)
        Initializes the agent, loads system prompts, and sets up conversation management.
    _get_formatted_time()
        Returns the current time formatted as a string in the 'America/Chicago' timezone.
    _load_file(file_path)
        Loads the contents of a file into a string.
    _save_messages()
        Saves the conversation history to a file in JSON format.
    _get_openai_response(messages, reasoning="mininmal", verbosity="low")
        Calls OpenAI's API to generate a response based on the provided conversation history.
    _print_messages(i=0)
        Prints the stored conversation messages along with metadata.
    _process_query(user_query)
        Processes a user query, retrieves domain knowledge if needed, and generates a response.
    _get_query_plus_comp_model_summary(user_query)
        Generates a summary of the user's query combined with their computational model for improved RAG retrieval.
    _get_dynamic_intro_string()
        Generates a dynamically rephrased introduction for the agent.
    _is_message_in_stop_words(message)
        Checks if a given message is in a predefined set of stop words.
    talk()
        Starts an interactive conversation with the user, processing queries until a termination command is given.
    _gui_respond(message, chat_history)
        Handles chatbot responses within the Gradio GUI.
    _talk_with_gui()
        Launches the Gradio-based GUI for user interaction.
    _end_conversation()
        Ends the conversation and handles cleanup tasks.

    Notes
    -----
    - The agent operates in either a development mode (loading a predefined student model) or a production mode.
    - The retrieval-augmented generation (RAG) component helps retrieve domain knowledge relevant to the user's query.
    - Conversation truncation is applied when the token limit is exceeded.
    - The agent supports both terminal-based and GUI-based interactions.
    """

    def __init__(self,use_gui=False):
                
        self.openai_client = openai.OpenAI()

        # Currently hard-coded but will need to be dynamic
        self.group = 0

        self.use_gui = use_gui
        self.RAG = RAG() 
        self.has_spoken = False

        self.messages = [{"role": "system", "content": self._load_file(Config.prompt_path)}]
        self.message_timestamps = [self._get_formatted_time()]
        self.running_word_count = len(self.messages[0]["content"].split())

        self.learner_model = LearnerModel()

        if Config.env == "dev":
            self.learner_model.user_model = self._load_file(f'test/g{Config.group}/test_student_model.txt')
        else:
            self.learner_model.user_model = ""
        logging.info(f"Successfully initialized Agent class in '{Config.env}' environment.")

        self.message_truncation_count = 0

    def _get_formatted_time(self):
        """
        Get the current time formatted as a string in Central Time (CT) with timezone details.

        The function retrieves the current UTC time, converts it to Central Time
        (America/Chicago), and formats it in the following format:
        'YYYY-MM-DD HH:MM:SS TZ±HHMM'.

        Returns
        -------
        str
            The formatted current time in Central Time with timezone information.
        """
        utc_now = datetime.datetime.now(pytz.utc)
        central_tz = pytz.timezone('America/Chicago')
        central_now = utc_now.astimezone(central_tz)
        formatted_time = central_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        return formatted_time

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
        
    def _save_messages(self):
        """
        Save the conversation messages to a file in JSON format.

        This method attempts to write the `messages` attribute to a file specified 
        by `convo_save_path` in JSON format with an indentation of 4 spaces. 
        If successful, it logs a confirmation message; otherwise, it logs an error.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        - This method logs a success message upon successful saving.
        - If an error occurs during file writing, it logs an error message.

        Raises
        ------
        Exception
            If an error occurs while writing to the file.
        """
        try:
            save_path = Config.convo_save_path+"/"+Config.c2stem_task+"_Group"+str(self.group)+"_"+epoch_time+"_CONVO.json"

            # Merge messages sent/received to/from OpenAI w/ timestamps
            save_messages = []
            for i in range(len(self.messages)):
                m = self.messages[i].copy()
                m["timestamp"] = self.message_timestamps[i]
                save_messages.append(m)

            with open(save_path, 'w') as f:
                json.dump(save_messages, f, indent=4)
                logging.info(f"Successfully saved conversation from Agent class to: '{save_path}'")
        except Exception as e:
            logging.error(f"Error saving conversation from Agent class to: '{save_path}': {e}")

    def _get_openai_response(self, messages, reasoning="low", verbosity="low"):
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
                response = self.openai_client.responses.create(
                    model=Config.model,
                    input=messages,
                    reasoning={"effort": reasoning},
                    text={"verbosity": verbosity}
                )
                logging.info(f"Successfully called OpenAI API in Agent class.'")
                return response.output_text
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
        
    def _print_messages(self,i=0):
        """
        Print the stored messages along with their roles and content.

        This method prints a formatted view of the conversation history, including the role of each message 
        (e.g., "system", "user", "assistant") and its content. It also displays summary statistics, such as 
        the total number of messages, the total word count, and the number of times messages have been truncated 
        due to token limitations.

        Parameters
        ----------
        i : int, optional
            The number of recent messages to display. If `i=0`, all messages are printed. Defaults to 0.

        Returns
        -------
        None
            This function only prints the messages and does not return a value.

        Notes
        -----
        - Messages are printed with a visual separator for clarity.
        - If `i` is greater than 0, only the last `i` messages are displayed.
        - The function displays conversation metadata such as the total message count, word count, and truncation count.
        - The total running word count helps monitor token usage in the conversation.
        """
       
        print("\n\n***************************************************************************")
        for m in self.messages[-i:]:
            print("------------------------------------------------------------------------")
            print("ROLE:", m["role"])
            print("CONTENT:", m["content"])
        print("------------------------------------------------------------------------")
        print(f"Total messages in list: {len(self.messages)}")
        print(f"Total word count for all messages: {self.running_word_count}")
        print(f"Truncation count: {self.message_truncation_count}")
        print("***************************************************************************\n\n")

    def _process_query(self, user_query):
        """
        Processes a user query, retrieves relevant domain knowledge, interacts with OpenAI's API, and updates the conversation.

        This method determines whether it's the first query in the conversation. If so, it retrieves domain knowledge
        using a retrieval-augmented generation (RAG) approach and appends relevant context to the system message.
        It then sends the conversation history to OpenAI's chat completion API, retrieves the response, and appends it 
        to the conversation.

        Parameters
        ----------
        user_query : str
            The user's input query to process.

        Returns
        -------
        None
            This method updates the internal conversation state but does not return a value.

        Notes
        -----
        - For the first query, the method retrieves domain knowledge using RAG and appends it to the system message.
        - For subsequent queries, only the user query and student model are included in the conversation history.
        - If the token count exceeds `Config.word_threshold`, older messages are truncated to fit within the model's limits.
        - Messages are logged and saved after processing.
        - The conversation history is maintained in `self.messages`, where each entry is a dictionary with keys "role" and "content".
        - The method sets `self.has_spoken` to `True` after the first query to indicate that the agent has responded.
        """
        if not self.has_spoken:
            # First query: Perform RAG retrieval, first summarize the user's query and computational model
            query_plus_comp_model_summary = self._get_query_plus_comp_model_summary(user_query)

            # Get embeddings
            q_embed = self.RAG.get_embeddings([query_plus_comp_model_summary])

            # Handle q_embed being None
            if q_embed is None:
                logging.error("Failed to retrieve embeddings in Agent class, using fallback domain context.")
                domain_context = "No domain knowledge available due to failed embedding retrieval."
            else:

                # Embedding retrieval successful
                q_embed = q_embed[0] 

                retrieval_result = self.RAG.retrieve(q_embed, 3)
                if retrieval_result is None or "matches" not in retrieval_result or not retrieval_result["matches"]:
                    logging.error("Failed to retrieve knowledge base matches in Agent class, using fallback domain context.")
                    domain_context = "No domain knowledge available currently due to failed RAG retrieval."
                else:

                    # Matches retrieved successfully
                    matches = retrieval_result["matches"]
                    domain_context = "\n\n".join([m["metadata"]["text"] for m in matches])

            # Save retrieved domain knowledge
            rag_retrieval_save_path = Config.retrieved_domain_knowledge_save_path+Config.c2stem_task+"_Group"+str(self.group)+"_"+epoch_time+"_RAG.json"

            try:
                with open(rag_retrieval_save_path, "a") as f:
                    domain_knowledge_dict = {
                        "timestamp": self._get_formatted_time(),
                        "query_logs_summary": query_plus_comp_model_summary,
                        "domain_knowledge_retrieved": domain_context,
                    }
                    json.dump(domain_knowledge_dict, f, indent=4)
                    logging.info(f"Saved retrieved domain knowledge in Agent class to: '{rag_retrieval_save_path}'")
            except Exception as e:
                logging.error(f"Error saving retrieved domain knowledge in Agent class to: '{rag_retrieval_save_path}': {e}")
            
            # Update messages with domain context (fallback or actual context)
            self.messages[0]["content"] += f"\n\nDomain Context:\n{domain_context}"
    
            # Create the initial user message and student model
            user_message_str = f"Student Query:\n{user_query}\n\n[CURRENT STUDENT MODEL]:\n{self.learner_model.user_model}"
        
        else:
            # Subsequent queries: only include the user query/response in the messages + computational model
            user_message_str = user_query
            user_message_str += f"\n\n[CURRENT STUDENT MODEL]:\n{self.learner_model.user_model}"
        
        self.messages.append({"role": "user", "content": user_message_str})
        self.message_timestamps.append(self._get_formatted_time())

        # Truncate messages if approaching token threshold for the model
        truncated_messages = [self.messages[0]]+self.messages[1+self.message_truncation_count:]

        # # To test truncation
        # if len(truncated_messages)!=len(self.messages):
        #     print("\n\n***************************************************************************")
        #     for m in [self.messages[0]]+self.messages[1+self.message_truncation_count:]:
        #         print("------------------------------------------------------------------------")
        #         print("ROLE:", m["role"])
        #         print("CONTENT:", m["content"])
        #     print("------------------------------------------------------------------------")
        #     print(f"Total messages in list: {len(self.messages)}")
        #     print(f"Total word count for all messages: {self.running_word_count}")
        #     print(f"Truncation count: {self.message_truncation_count}")
        #     print("***************************************************************************\n\n")

        response_text = self._get_openai_response(truncated_messages)
        if not self.use_gui: 
            print(f"\n{Config.agent_name}: {response_text}\n")
        self.messages.append({"role": "assistant", "content": response_text})
        self.message_timestamps.append(self._get_formatted_time())

        self.running_word_count += \
            len(self.messages[-2]["content"].split()) + \
            len(self.messages[-1]["content"].split())
        
        if self.running_word_count > Config.word_threshold:
            self.message_truncation_count += 2

            # To test truncation
            # print(f"TRUNCATED NOW {self.message_truncation_count}")

        self._print_messages(2)
        self._save_messages()

        # Set flag to indicate that the agent has spoken
        if not self.has_spoken:
            self.has_spoken = True

    def _get_query_plus_comp_model_summary(self, user_query):
        """
        Summarizes the user's query and compares it with the student's computational model to identify the student's issue
        and determine the domain knowledge that should be retrieved via RAG to help them progress.

        This method invokes the OpenAI API using few-shot in-context learning to get a one-paragraph summary of the student's state for improved
        RAG retrieval relative to simply retrieving documents based solely on the query.

        Parameters
        ----------
        user_query : str
            The user's query for which the summary is to be generated (in conjunction with their computational model derived from the logs).

        Returns
        -------
        summary : str
            The summary generated by the OpenAI API to be used for RAG retrieval in the `_process_query` method.

        Notes
        -----
        - Few-shot examples are loaded from a JSON file specified by `Config.summary_few_shot_instances_path`.
        - The system prompt is loaded from a file specified by `Config.rag_summary_prompt_path`.
        - The conversation is formatted according to OpenAI's chat completion API, with roles such as 'system', 'user', and 'assistant'.
        - The method `_get_openai_response` is used to interact with the OpenAI API and retrieve the summary.
        """
        summary_messages = [{"role": "system", "content": self._load_file(Config.rag_summary_prompt_path)}]

        with open(Config.summary_few_shot_instances_path, 'r') as f:
            few_shot_instances = json.load(f) 
        for inst in few_shot_instances:
            student_group = inst["student_group"]
            student_query = inst["user_query"]
            student_computational_model = inst["student_computational_model"]
            assistat_response = inst["assistant_response"]

            group_query_model_string = f"Student Group:\n{student_group}\n\Student Query:\n{student_query}\n\nStudent Computational Model:\n{student_computational_model}"
            summary_messages.append({"role": "user", "content": group_query_model_string})
            summary_messages.append({"role": "assistant", "content": assistat_response})
        
        current_group_query_model_string = f"Student Group:\n1\n\Student Query:\n{user_query}\n\nStudent Computational Model:\n{self.learner_model.user_model}"
        summary_messages.append({"role": "user", "content": current_group_query_model_string})

        summary = self._get_openai_response(summary_messages)
        logging.info(f"\n\nRetrieved the following summary of the students' current problem in the Agent class: {summary}\n\n")
        return summary
       
    def _get_dynamic_intro_string(self):
        """
        Generates a dynamically rephrased introduction string using an OpenAI response.

        Returns
        -------
        str
            A rephrased introduction string generated by the OpenAI model.
        """
        intro_str = f"Hi, I'm {Config.agent_name}, a collaborative peer agent! Is there something I can help you with?"
        intro_str_rephrase = self._get_openai_response(
            messages=
                [
                    {"role": "system", "content": "Rephrase this introduction with no formatting and only once:\n"},
                    {"role": "user", "content": intro_str}
                ]
        )
        return intro_str_rephrase
    
    def _is_message_in_stop_words(self, message):
        """
        Check if a message is in the predefined set of stop words.

        Parameters
        ----------
        message : str
            The message string to check against the stop words set.

        Returns
        -------
        bool
            `True` if the message is in the set of stop words, `False` otherwise.
        """
        return message in {}
        # return message in {"q", "quit", "stop", "end"}

    def talk(self):
        """
        Starts an interactive conversation with the user and continues until a termination command is given.

        This function defers to `_talk_with_gui` if `use_gui` is set to `True`.
        """
        if self.use_gui:
            self._talk_with_gui()
            return
        
        intro_str = self._get_dynamic_intro_string()
        
        user_query = input(f"\n{Config.agent_name}: "+intro_str+"\n\n"+"Student: ").lower()

        # if self._is_message_in_stop_words(user_query):
        #     self._end_conversation()
        #     return

        # Process the first query
        self._process_query(user_query)

        # Loop to process further queries
        while not self._is_message_in_stop_words((new_query := input("Student: ").lower())):
            self._process_query(new_query)

        # self._end_conversation()
    
    def _gui_respond(self, message, chat_history):
        """
        Handles the chatbot's response to a user message within the Gradio GUI.

        Parameters
        ----------
        message : str
            The user's input message.
        chat_history : list of lists
            The current chat history, where each entry is a tuple containing the user's message and the chatbot's response.

        Returns
        -------
        str
            An empty string to reset the message input field.
        chat_history : list of tuples
            The updated chat history, with the new user message and the chatbot's response appended.
        """
        self._process_query(message)
        bot_message = self.messages[-1]["content"]
        chat_history.append((message, bot_message))
        return "",chat_history
    
    def _talk_with_gui(self):
        """
        Launches the Gradio GUI for interacting with the agent.
        """
        with gr.Blocks() as demo:
            with gr.Row():
                # Image c/o FlatIcon.com:
                #   https://www.flaticon.com/free-icon/student_257651
                gr.Image(
                    "peer_agent_image.png",
                    width=100,
                    height=100,
                    show_label=False,show_download_button=False,show_fullscreen_button=False,\
                        show_share_button=False,interactive=False
                )

            gr.Markdown(
                "<h2 style='text-align:center'>"
                "Copa: A Collaborative Peer Agent for C2STEM"
                "</h2>"
            )
            greeting = self._get_dynamic_intro_string()
            chatbot = gr.Chatbot(height=240,value=[[None, greeting]],show_label=False)

            msg = gr.Textbox(label="Message")
            msg.submit(self._gui_respond, inputs=[msg, chatbot], outputs=[msg, chatbot]) #Press enter to submit

            send_btn = gr.Button("Send")
            send_btn.click(self._gui_respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

            # end_btn = gr.Button("End Conversation")
            # end_btn.click(self._end_conversation)

        demo.launch(share=False,inbrowser=False)
    
    def _end_conversation(self):
        """
        Terminates the conversation and handles any cleanup tasks.
        """
        self._print_messages()
        os._exit(0)
