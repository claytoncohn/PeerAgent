from RAG import RAG
import os
from dotenv import load_dotenv
load_dotenv()
import openai

class Agent:
    def __init__(self):
        self.name = os.getenv("AGENT_NAME")

        self.RAG = RAG()

        self.ENV = os.getenv("ENV")
        if self.ENV == "dev":
            self.student = os.getenv("STUDENT")

            # These will be dynamic once AST parsing is up and running
            # Currently, this points to the 2021 SSMV data (G9) when the students' truck started going backwards
            with open(f'test/{self.student}/test_student_model.txt') as f:
                self.student_model = "".join([line for line in f])
            with open(f'test/{self.student}/test_task_context.txt') as f:
                self.task_context = "".join([line for line in f])

        self.model = os.getenv("CHAT_MODEL")
        PROMPT_PATH = os.getenv("PROMPT_PATH")
        with open(PROMPT_PATH) as f:
            self.prompt = "".join([line for line in f])

        self.messages = [
            {"role":"system", "content":self.prompt},
        ]

        self.domain_context = ""

        # Create RAG instance
        self.rag = RAG()

        # Track if this is the first part of the conversation
        self.has_spoken = False

    def print_messages(self):
        for m in self.messages:
            print("------------------------------------------------------------------------")
            print("ROLE:",m["role"])
            content = m["content"]
            print("CONTENT:")
            for line in content.split("\n"):
                print(line)

    def talk(self):
        intro_str = """
        --------------------------------------
        I'm Copa, a collaborative peer agent! 

        What can I help you with?
        --------------------------------------
        """
        user_query = input(intro_str).lower()

        # Do RAG retrieval here if first query for session
        if not self.has_spoken:

            # Domain knowledge from knowledge base (RAG retrieval)
            q_embed = self.RAG.get_embeddings(user_query)[0]
            k = 3
            matches = self.RAG.retrieve(q_embed,k)["matches"]
            domain_context = "\n\n".join([m["metadata"]["text"] for m in matches])
            
            # Add to system prompt
            self.messages[0]["content"] += "\n\nDomain Context:\n" + domain_context

        # Task context, user query, and computational model
        user_prompt_str = "Task Context:\n" + self.task_context + "\n\nStudent Query:\n" + user_query + "\n\nStudent Computational Model:\n" + self.student_model
        self.messages.append(
            {"role":"user","content":user_prompt_str}
        )
        
        response = openai.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages = self.messages
        )
        response_text = response.choices[0].message.content
        print("\n" + self.name + ": " + response_text,"\n")
        self.messages.append(
            {"role":"assistant","content":response_text}
        )

        self.has_spoken = True

        while (new_query := input().lower()) not in {"q","quit","stop","end"}:
            self.messages.append(
                {"role":"user","content":new_query}
            )

            response = openai.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages = self.messages
            )
            
            response_text = response.choices[0].message.content
            print("\n" + self.name + ": " + response_text,"\n")
            self.messages.append(
                {"role":"assistant","content":response_text}
            )
        else:
            if self.ENV == "dev":
                self.print_messages()
