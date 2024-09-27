
from RAG import RAG
import os
from dotenv import load_dotenv
import openai

load_dotenv()

class Agent:
    def __init__(self):
        self.name = os.getenv("AGENT_NAME", "Copa")
        self.RAG = RAG() 
        self.ENV = os.getenv("ENV", "dev")
        self.model = os.getenv("CHAT_MODEL", "gpt-4o")
        self.has_spoken = False
        self.messages = [{"role": "system", "content": self._load_file(os.getenv("PROMPT_PATH"))}]
        self.domain_context = ""

        if self.ENV == "dev":
            self.student = os.getenv("STUDENT", "1")

            # These will be dynamic once AST parsing is up and running
            # Currently, this points to the 2021 SSMV data (G9) when the students' truck started going backwards
            self.student_model = self._load_file(f'test/{self.student}/test_student_model.txt')
            self.task_context = self._load_file(f'test/{self.student}/test_task_context.txt')

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
                return f.read()
        except (FileNotFoundError, IOError):
            print(f"Error: File '{file_path}' not found.")
            return ""

    def _get_openai_response(self, messages):
        """
        Helper function to call OpenAI API and return the response.

        Parameters
        ----------
        messages : list
            List of conversation messages.

        Returns
        -------
        str
            Assistant's response or an error message.
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages=messages
            )
            return response.choices[0].message.content
        except openai.error.OpenAIError as e:
            print(f"Error during OpenAI API call: {e}")
            return "OpenAI API call failure."
        
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
            try:
                q_embed = self.RAG.get_embeddings(user_query)[0]
                matches = self.RAG.retrieve(q_embed, 3)["matches"]
                domain_context = "\n\n".join([m["metadata"]["text"] for m in matches])
                self.messages[0]["content"] += f"\n\nDomain Context:\n{domain_context}"
            except Exception as e:
                print(f"Error during RAG retrieval: {e}")
        
        # Create the user prompt including task context and student model
        if self.ENV == "dev":
            if not self.task_context or not self.student_model:
                print("Warning: Task context or student model missing.")
            user_prompt_str = f"Task Context:\n{self.task_context}\n\nStudent Query:\n{user_query}\n\nStudent Computational Model:\n{self.student_model}"
        else:
            user_prompt_str = f"User Query:\n{user_query}"
        
        self.messages.append({"role": "user", "content": user_prompt_str})

        # Get and print assistant response
        response_text = self._get_openai_response(self.messages)
        print(f"\n{self.name}: {response_text}\n")
        self.messages.append({"role": "assistant", "content": response_text})
        self.has_spoken = True

    def talk(self):
        """
        Starts an interactive conversation with the user and continues until a termination command is given.
        """
        intro_str = """
        --------------------------------------
        I'm Copa, a collaborative peer agent! 

        What can I help you with?
        --------------------------------------
        """
        user_query = input(intro_str).lower()

        # Process the first query
        self._process_query(user_query)

        # Loop to process further queries
        while (new_query := input().lower()) not in {"q", "quit", "stop", "end"}:
            self._process_query(new_query)

        # Optionally print messages in 'dev' environment
        if self.ENV == "dev":
            self.print_messages()