import os
from dotenv import load_dotenv
load_dotenv()
import openai

class Agent:
    def __init__(self):
        self.model = os.getenv("CHAT_MODEL")
        with open('text/prompt_v1.txt') as f:
            self.prompt = "".join([line for line in f])

        # This will be dynamic once AST parsing is up and running
        # Currently, this points to the 2021 SSMV data (G9) when the students' truck started going backwards
        with open('text/student_model.txt') as f:
            self.student_model = "".join([line for line in f])

        # This will be dymamic once RAG retrieval implemented
        # Currently this points to relevant part of knowledge base
        with open('text/domain_context.txt') as f:
            self.domain_context = "".join([line for line in f])

        self.messages = [
            {"role":"system", "content":self.prompt},
        ]

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
I am collaborative peer agent! 

What can I help you with?
--------------------------------------
        """
        user_query = input(intro_str).lower()
        if not self.has_spoken:
            # Domain knowledge from knowledge base
            domain_context = "\n\nDomain Context:\n" + self.domain_context
            self.messages[0]["content"] += domain_context

            # User query and computational model
            user_prompt_str = "Student Query:\n" + user_query + "\n\nStudent Computational Model:\n" + self.student_model
        self.messages.append(
            {"role":"user","content":user_prompt_str}
        )
        
        response = openai.chat.completions.create(
                model=self.model,
                temperature=0.0,
                messages = self.messages
        )
        response_text = response.choices[0].message.content
        print("\nAssistant:",response_text,"\n")
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
            print("\nAssistant:",response_text,"\n")
            self.messages.append(
                {"role":"assistant","content":response_text}
            )
        else:
            self.print_messages()
