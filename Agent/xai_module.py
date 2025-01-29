import json
import logging

class XAI_module:
    """
    A separate class for tracking and analyzing the student's knowledge state.

    Responsibilities:
    - Stores and manages known knowns, known unknowns, and unknown unknowns.
    - Uses Chain of Thought (CoT) reasoning to analyze conversation history.
    - Ensures structured JSON updates without redundancy.
    """

    def __init__(self):
        """Initialize the knowledge state with empty sets."""
        self.knowledge_state = {
            "known_knowns": set(),
            "known_unknowns": set(),
            "unknown_unknowns": set()
        }

    def analyze_messages(self, messages, get_openai_response):
        """
        Uses Chain of Thought reasoning to analyze conversation history and update the knowledge state.

        Parameters:
        ------------
        messages : list
            List of conversation messages from the Agent.
        get_openai_response : function
            Function to call the OpenAI API and return a response.

        Updates:
        ------------
        - Completely replaces the knowledge state with a newly generated version.
        """

        # Format the conversation history
        conversation_history = "\n\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in messages])

        # Convert current knowledge state to JSON
        current_knowledge_json = json.dumps({
            "known_knowns": list(self.knowledge_state["known_knowns"]),
            "known_unknowns": list(self.knowledge_state["known_unknowns"]),
            "unknown_unknowns": list(self.knowledge_state["unknown_unknowns"])
        }, indent=4)

        analysis_prompt = [
            {"role": "system", "content": "You are an AI tutor analyzing a student's thought process based on their conversation history."},
            {"role": "user", "content": f"""
            A student is learning physics through coding simulations. Here is their conversation history so far:

            ---- Conversation History ----
            {conversation_history}
            ---- End of Conversation ----

            Here is their current knowledge state:
            ```json
            {current_knowledge_json}
            ```

            ## Step 1: Chain of Thought Analysis
            Before updating the knowledge state, analyze the conversation **step-by-step** by answering the following:
            1. What mistakes did the student make?
            2. What reasoning errors are evident in their approach?
            3. Which concepts does the student correctly understand (known knowns)?
            4. Which concepts does the student struggle with but recognizes their lack of knowledge in (known unknowns)?
            5. Which misconceptions does the student hold that they are unaware of (unknown unknowns)?

            Provide your reasoning in a structured way:

            ```
            Mistakes: ...
            Reasoning Errors: ...
            Known Knowns: ...
            Known Unknowns: ...
            Unknown Unknowns: ...
            ```

            ## Step 2: Updated Knowledge State
            Now, **based on your reasoning**, update the student's knowledge state.
            Your response must be in valid JSON format, following this exact structure:
            {{
                "known_knowns": ["updated_concept1", "updated_concept2", ...],  
                "known_unknowns": ["updated_concept3", "updated_concept4", ...],  
                "unknown_unknowns": ["updated_concept5", "updated_concept6", ...]  
            }}

            **Important:** Ensure that the response is strictly valid JSON with no extra text.
            """}
        ]
        
        response_text = get_openai_response(analysis_prompt)

        # Validate and replace knowledge state
        try:
            updated_state = json.loads(response_text)
            
            if isinstance(updated_state, dict) and all(k in updated_state for k in ["known_knowns", "known_unknowns", "unknown_unknowns"]):
                # Replace the entire knowledge state with the new one
                self.knowledge_state = {
                    "known_knowns": set(updated_state["known_knowns"]),
                    "known_unknowns": set(updated_state["known_unknowns"]),
                    "unknown_unknowns": set(updated_state["unknown_unknowns"])
                }
                logging.info(f"Knowledge state updated successfully: {json.dumps(self.knowledge_state, indent=4)}")
            else:
                logging.error(f"Invalid JSON structure received from OpenAI: {updated_state}")

        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON from OpenAI response: {e}\nResponse Text: {response_text}")

    def get_knowledge_state(self):
        """
        Returns the current knowledge state.

        Returns:
        ------------
        dict : The latest knowledge state in a JSON-friendly format.
        """
        return {
            "known_knowns": list(self.knowledge_state["known_knowns"]),
            "known_unknowns": list(self.knowledge_state["known_unknowns"]),
            "unknown_unknowns": list(self.knowledge_state["unknown_unknowns"])
        }


    #TODO: implement this
    def suggest_learning_milestones(self, messages, get_openai_response):
        """
        Based on the chat log and student's knowledge state, suggest the next learning milestone
        to complete the task.
        
        Parameters:
        ------------
        messages : list
            List of conversation messages from the Agent.
        get_openai_response : function
            Function to call the OpenAI API and return a response.

        Returns:
        ------------
        - returns learning milestones based on the student's KS and chat log
        
        output example:
        The next learning goal milestone for the student should be:

        1. **Understand and Correct the Gravitational Force Calculation**: 
        - Focus on reinforcing the concept of Newton's law of universal gravitation, particularly the inverse-square law component. 
        - Correct the code to ensure that the force magnitude is calculated using the square of the distance.

        2. **Learn and Apply Numerical Integration Methods**: 
        - Study the Euler method and its variants (semi-implicit, Verlet, Runge-Kutta) to properly update position and velocity. 
        - Implement a standard Euler integration method without scaling factors like 0.5, understanding how numerical integration works in simulations.

        3. **Explore the Impact of Numerical Errors**: 
        - Investigate how inaccuracies in force calculation and integration methods affect the simulation's stability and results.
        - Simulate with various time steps to see the effect on accuracy and gain insight into numerical stability issues.

        These milestones will solidify foundational concepts while addressing the specific coding and physical modeling errors currently present.
        
        """
        return ""
    
    #TODO: implement this
    def generate_guiding_questions(self, messages, get_openai_response, milestone=""):
        """
        Based on the chat log, student's knowledge state, and milestone(optional) return a list of guiding questions
        just like what you see on other LLM based products. I recommend using JSON format for this.
        
        The goal here is to basically teach students "learn to ask questions" or "teach how to fish" so we provide
        what kind of questions they should be asking if they don't know what they are doing.
        
        output sample:
        
          "guiding_questions": [
                "What is the correct formula for calculating gravitational force according to Newton's law of universal gravitation?",
                "How does the distance between two objects affect the gravitational force between them?",
                "What are the differences between the standard Euler method and other numerical integration methods like Runge-Kutta or Verlet?",
                "How does the choice of numerical integration method affect the stability and accuracy of a simulation?",
                "Why is it important to square the distance when calculating gravitational forces?",
                "What are some common causes of instability in n-body simulations?",
                "How can you test if your simulation is correctly implementing the laws of physics?",
                "What impact does timestep size have on the results of a numerical simulation?",
                "How can numerical errors accumulate in simulations, and what are strategies to minimize them?"
            ]
        
        Parameters:
        ------------
        messages : list
            List of conversation messages from the Agent.
        get_openai_response : function
            Function to call the OpenAI API and return a response.
        milestone:
            basically the "next step" the student should achieve to reach the goal (solving the problem)
        
        Returns:
        ------------
        list of guiding questions
        """
        
        
        

    # suggest possible questions to ask based on the knowledge base
    # as the suggestions on the bottom