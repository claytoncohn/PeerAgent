import json
import logging

class XAI_module:
    """
    A separate class for tracking and analyzing the student's knowledge state.
    
    Responsibilities:
    - Stores the educational concepts that the student needs to know.
    - Manages the current knowledge state of the student.
    - Uses Chain of Thought (CoT) reasoning internally to analyze conversation history.
    - Ensures structured JSON updates without redundancy.
    """

    def __init__(self, problem, editorial):
        """
        Initialize the knowledge state with empty sets.
        """
        self.problem = problem
        self.editorial = editorial
        self.concepts = []
        
        # knowledge_state: dictionary mapping concept -> 0 (unknown) or 1 (known)
        self.knowledge_state = {}
        
        # summary: human-readable summary of the student's current knowledge state
        self.summary = ""
        

    def _analyze_problem(self, problem_description, editorial, get_openai_response):
        """
        Uses Chain of Thought reasoning to analyze the problem description and editorial in order to define
        a set of concepts that the student needs to know for K-12 education.
        
        Parameters:
            problem_description (str): The problem description provided to the student.
            editorial (str): The editorial solution to the problem.
            get_openai_response (function): Function to call the OpenAI API and return a response.
        
        Updates:
            - Sets self.concepts to a list of concepts extracted.
            - Initializes self.knowledge_state as a dictionary mapping each concept to 0.
        """
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an educational content analyzer specializing in K-12 material. "
                    "Your task is to carefully analyze the provided problem description and its editorial solution. "
                    "Using internal chain-of-thought reasoning, determine all essential educational concepts that a student must understand to solve the problem. "
                    "Output ONLY a valid JSON with exactly two keys: 'reasoning' (string) and 'concepts' (a list of strings). "
                    "Ensure that your output contains no extraneous text and is safe and appropriate for a K-12 educational environment. "
                    "You can assume that the concepts are single words or short phrases."
                    "You can also assume that the students are beginners in the subject area and need to learn the basic concepts to solve the problem."
                    ""
                )
            },
            {
                "role": "user",
                "content":
                    f"""
                    Here is the problem description and editorial solution for a K-12 educational problem:
                    
                    <Problem Description>
                    {problem_description}
                    </Problem Description>
                    
                    <Editorial>
                    {editorial}
                    </Editorial>
                    
                    ## Step 1: Chain of Thought Analysis
                    Before creating the concepts, we need to analyze the problem description and editorial solution to extract the essential educational concepts.
                    Provide your reasoning as a string in JSON format with key 'reasoning'.
                    
                    ## Step 2: Extract Concepts
                    Extract the essential educational concepts that a student must understand to solve the problem. Your response must be in valid JSON format.
                    """
                
            }
        ]
        
        response_text = get_openai_response(prompt)
        
        try:
            result = json.loads(response_text)
            self.concepts = result.get("concepts", [])
            self.knowledge_state = result.get("knowledge_state", {})
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response in _analyze_problem: {e}\nResponse Text: {response_text}")


    def analyze_messages(self, messages, get_openai_response):
        """
        Uses Chain of Thought reasoning to analyze conversation history and update the knowledge state and summary.

        Parameters:
            messages (list): List of conversation messages from the Agent.
            get_openai_response (function): Function to call the OpenAI API and return a response.

        Updates:
            - Completely replaces self.knowledge_state and self.summary with a newly generated version.
        """
        # Format the conversation history as a string.
        conversation_history = "\n\n".join(
            [f"{m['role'].capitalize()}: {m['content']}" for m in messages]
        )
        
        # Convert the current knowledge state to a JSON string.
        current_knowledge_json = json.dumps(self.knowledge_state, indent=4)
        
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an educational assistant with expertise in analyzing student interactions in a K-12 setting. "
                    "Your task is to review the conversation history and the student's previous knowledge state. "
                    "Use chain-of-thought reasoning to update the summary and update the student's knowledge state based on the dialogue. "
                    "Output ONLY a valid JSON with exactly two keys: 'summary' (a concise string summary) and 'knowledge_state'."
                    "Ensure your output is safe and appropriate for an educational context."
                )
            },
            {
                "role": "user",
                "content":
                    f"""
                    Here are the conversation history and the student's current knowledge state:
                    
                    <Conversation History>
                    {conversation_history}
                    </Conversation History>
                    
                    <Current Knowledge State>
                    {current_knowledge_json}
                    </Current Knowledge State>
                    
                    <Current Student Summary>
                    {self.summary}
                    </Current Student Summary>
                    
                    Your response must be in valid JSON format, following this exact structure:
                    {{
                        "summary": "...",
                        "knowledge_state": {{...}}
                        
                    }}.
                    Make sure not to add or delete additional concepts from the knowledge state.
                    """
            }
        ]
        
        response_text = get_openai_response(prompt)
        
        try:
            result = json.loads(response_text)
            self.knowledge_state = result.get("knowledge_state", {})
            self.summary = result.get("summary", "")
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response in analyze_messages: {e}\nResponse Text: {response_text}")


    def get_knowledge_state(self):
        """
        Returns the current knowledge state.

        Returns:
            dict: The latest knowledge state in a JSON-friendly format.
        """
        return self.knowledge_state


    def suggest_explanations(self, messages, get_openai_response):
        """
        Based on the chat log and student's knowledge state, return a set of explanations that the student
        might need to understand the problem better.
        
        Parameters:
            messages (list): List of conversation messages from the Agent.
            get_openai_response (function): Function to call the OpenAI API and return a response.
        
        Returns:
            list: A list of explanation strings (learning milestones) based on the student's knowledge state and chat log.
        """
        conversation_history = "\n\n".join(
            [f"{m['role'].capitalize()}: {m['content']}" for m in messages]
        )
        current_knowledge_json = json.dumps(self.knowledge_state, indent=4)
        
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a highly experienced educational assistant. Your role is to review a student's conversation log and current knowledge state to identify learning gaps. "
                    "Use chain-of-thought reasoning to update the summary and update the student's knowledge state based on the dialogue. "
                    "Output ONLY a valid JSON with two keys: 'reasoning', which contains the chain-of-thought string, and 'explanations', which should be a dictionary where keys are concepts and values are explanations. "
                    "Ensure all suggestions are appropriate and safe for K-12 education."
                )
            },
            {
                "role": "user",
                "content":
                    f"""
                    Here are all the relevant details to suggest explanations to the student:
                    
                    <Problem Description>
                    {self.problem}
                    </Problem Description>
                    
                    <Editorial>
                    {self.editorial}
                    </Editorial>
                    
                    <Conversation History>
                    {conversation_history}
                    </Conversation History>
                    
                    <Current Knowledge State>
                    {current_knowledge_json}
                    </Current Knowledge State>
                    
                    Based on the student's knowledge state and the conversation history, suggest explanations (learning milestones) that the student might need to understand the problem better.
                    
                    Specifically, follow these steps:
                    1. Find concepts that are marked as zero in the knowledge state. They are the concepts the student doesn't know.
                    2. For each concept, think step-by-step how to explain it to the student using all the information available.
                    3. Provide a JSON response with 'reasoning' and 'explanations' keys.
                    
                    Your response must be in valid JSON format, following this exact structure:
                    {{  
                        "reasoning": "...",
                        "explanations": {{
                            "concept1": "explanation1",
                            "concept2": "explanation2",
                            ...
                        }}
                    }}
                    """
            }
        ]
        
        response_text = get_openai_response(prompt)
        
        try:
            result = json.loads(response_text)
            explanations = result.get("explanations", [])
            return explanations
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response in suggest_explanations: {e}\nResponse Text: {response_text}")
            return []
