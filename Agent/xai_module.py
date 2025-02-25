import json
import logging

class XAI_module:
    """
    A separate class for tracking and analyzing the student's knowledge state.

    Responsibilities:
    - Stores concepts and syntaxes that the the student needs to know
    - Manages the current knowledge state of the student represented as 
    - Uses Chain of Thought (CoT) reasoning to analyze conversation history.
    - Ensures structured JSON updates without redundancy.
    """

    def __init__(self, problem, editorial):
        """Initialize the knowledge state with empty sets."""
        self.problem = problem
        self.editorial = editorial
        self.concepts = []
        self.syntaxes = []
        
        # knowledge state is a binary dictionary of concepts, 0 for unknown, 1 for known
        self.knowledge_state = {}
        
        # summary of the student's knowledge state in a human-readable format
        self.summary = ""
        
    def _analyze_problem(self, problem_description, editorial):
        """
        Uses Chain of Thought reasoning to analyze the problem description and editorial in order to define
        a set of concepts and syntaxes that the student needs to know to solve the problem for K-12 education.
        
        Parameters:
        ------------
        problem_description : str
            The problem description provided to the student.
            
        editorial : str
            The editorial solution to the problem.
        
        Updates:
        ------------
        - Updates the concepts and syntaxes that the student needs to know.
        - Updates the knowledge state of the student.
        """
        # TODO
        # Analyze the problem description and editorial to extract concepts and syntaxes
        # Update the concepts and syntaxes that the student needs to know
        # initialize knowledge state with 0 for all concepts and syntaxes
        pass
    
    
    def analyze_messages(self, messages, get_openai_response):
        """
        Uses Chain of Thought reasoning to analyze conversation history and update the knowledge state and summary.

        Parameters:
        ------------
        messages : list
            List of conversation messages from the Agent.
        get_openai_response : function
            Function to call the OpenAI API and return a response.

        Updates:
        ------------
        - Completely replaces the knowledge state and summary with a newly generated version.
        """

        # Format the conversation history
        conversation_history = "\n\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])

        previous_knowledge_state = self.knowledge_state
        
        previous_summary = self.summary
        
        # Convert current knowledge state to JSON
        prev_knowledge_json = json.dumps(previous_knowledge_state, indent=4)
        
        
        # TODO: implement the analysis prompt
        analysis_prompt = []
        
        response_text = get_openai_response(analysis_prompt)

        # Validate and replace knowledge state
        try:
            # TODO: implement the response parsing logic
            pass
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response: {e}\nResponse Text: {response_text}")

    def get_knowledge_state(self):
        """
        Returns the current knowledge state.

        Returns:
        ------------
        dict : The latest knowledge state in a JSON-friendly format.
        """
        return self.knowledge_state


    #TODO: implement this
    def suggest_explanations(self, messages, get_openai_response):
        """
        Based on the chat log and student's knowledge state, return a set of explanations that the student
        might need to understand the problem better.
        
        Parameters:
        ------------
        messages : list
            List of conversation messages from the Agent.
        get_openai_response : function
            Function to call the OpenAI API and return a response.

        Returns:
        ------------
        - returns learning milestones based on the student's knowledge state and chat log
        
        """
        return ""

        
        

    # suggest possible questions to ask based on the knowledge base
    # as the suggestions on the bottom