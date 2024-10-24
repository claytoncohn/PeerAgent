
from RAG import RAG
from dotenv import load_dotenv
import os
from globals import Config
import openai
import logging
import time
import gradio as gr
import json
logging.info("Successfully imported Agent class libraries.")

load_dotenv()

logging.basicConfig(level=logging.INFO)

class Agent:
    """
    A collaborative "knowledgeable peer" agent that interacts with users using RAG (Retrieval Augmented Generation)
    and OpenAI's chat completions API.

    The Agent class is responsible for:
    - Managing conversation flow.
    - Loading system prompts and student models based on the environment.
    - Retrieving domain knowledge using a RAG instance and augmenting user queries with log-based summaries of student difficulties.
    - Communicating with OpenAI's API to generate conversational responses.

    Attributes
    ----------
    use_gui : bool
        A flag indicating whether the agent should use a GUI for interaction.
    RAG : RAG
        An instance of the RAG class for handling retrieval-augmented generation for domain knowledge.
    has_spoken : bool
        A flag indicating whether the agent has already spoken in the current conversation.
    messages : list
        A list of dictionaries representing the conversation history.
    student_model : str, optional
        The student's computational model, loaded from a file, used in "dev" mode for testing.
    """
    def __init__(self,use_gui=False):
        self.use_gui = use_gui
        self.RAG = RAG() 
        self.has_spoken = False
        self.messages = [{"role": "system", "content": self._load_file(Config.prompt_path)}]

        if Config.env == "dev":
            self.student_model = self._load_file(f'test/g{Config.group}/test_student_model.txt')
        else:
            # This will be dynamic in production, but right now will have same values as in dev
            self.student_model = self._load_file(f'test/g{Config.group}/test_student_model.txt')
        logging.info("Successfully initialized Agent class.")

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
        
    def _print_messages(self,messages):
        """
        Prints the entire message history of the conversation.
        """
        for m in messages:
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
            query_plus_comp_model_summary = self._get_query_plus_comp_model_summary(user_query)
            q_embed = self.RAG.get_embeddings([query_plus_comp_model_summary])[0]
            matches = self.RAG.retrieve(q_embed, 3)["matches"]
            domain_context = "\n\n".join([m["metadata"]["text"] for m in matches])
            self.messages[0]["content"] += f"\n\nDomain Context:\n{domain_context}"
    
            # Create the initial user message and student model
            user_message_str = f"Student Query:\n{user_query}\n\nStudent Computational Model:\n{self.student_model}"
        else:
            # Subsequent queries: only include the user query/response in the messages
            user_message_str = user_query
        
        self.messages.append({"role": "user", "content": user_message_str})

        # Get and print assistant response
        response_text = self._get_openai_response(self.messages)
        if not self.use_gui: 
            print(f"\n{Config.agent_name}: {response_text}\n")
        self.messages.append({"role": "assistant", "content": response_text})

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

            group_query_model_string = f"Student Group:\n{student_group}\n\nUser Query:\n{student_query}\n\nStudent Computational Model:\n{student_computational_model}"
            summary_messages.append({"role": "user", "content": group_query_model_string})
            summary_messages.append({"role": "assistant", "content": assistat_response})
        
        current_group_query_model_string = f"Student Group:\n1\n\nUser Query:\n{user_query}\n\nStudent Computational Model:\n{self.student_model}"
        summary_messages.append({"role": "user", "content": current_group_query_model_string})

        summary = self._get_openai_response(summary_messages)
        logging.info(f"Retrieved the following summary of the students' current problem in the Agent class: {summary}")
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
                    {"role": "system", "content": "Rephrase this introduction:\n"},
                    {"role": "user", "content": intro_str}
                ],
            temperature=0.5
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
        stop_words = {"q", "quit", "stop", "end"}
        if message in stop_words:
            return True

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

        if self._is_message_in_stop_words(user_query):
            self._end_conversation()
            return

        # Process the first query
        self._process_query(user_query)

        # Loop to process further queries
        while not self._is_message_in_stop_words((new_query := input("Student: ").lower())):
            self._process_query(new_query)

        self._end_conversation()

    
    def _gui_respond(self,message, chat_history):
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
            gr.Markdown("""<h1><center>Copa: A Collaborative Peer Agent for C2STEM</center></h1>""") 
            greeting = self._get_dynamic_intro_string()
            chatbot = gr.Chatbot(height=240,value=[[None, greeting]],show_label=False)

            msg = gr.Textbox(label="Message")
            msg.submit(self._gui_respond, inputs=[msg, chatbot], outputs=[msg, chatbot]) #Press enter to submit

            send_btn = gr.Button("Send")
            send_btn.click(self._gui_respond, inputs=[msg, chatbot], outputs=[msg, chatbot])

            end_btn = gr.Button("End Conversation")
            end_btn.click(self._end_conversation)

        demo.launch(share=True)

    def _end_conversation(self):
        """
        Terminates the conversation and handles any cleanup tasks.
        """
        # Optionally print messages in 'dev' environment once conversation ends
        if Config.env == "dev":
            self._print_messages(self.messages)
        os._exit(0)