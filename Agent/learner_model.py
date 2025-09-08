from collections import deque

class LearnerModel:
    """
    Learner model of students using C2STEM. This tracks things like the students' computational model state and actions.
    The learner model will be used for dialogue management and guiding agent conversations to personalze student-agent interactions.

    Attributes
    ----------
    user_model : str
        A string representing the students' current computational model in C2STEM.
    actions : deque
        A deque of the last N actions (defined in .env) taken by the student in the C2STEM environment. 
        Each action is represented as a dictionary with keys "time", "type", and "block".
    model_score : int
        A score representing the quality of the student's computational model.

    Methods
    -------
    print_model_state()
        Prints the current state of the C2STEM model.
    print_actions()
        Prints the list of the last N actions (defined in .env) taken by the student in the C2STEM environment.
    """
    def __init__(self):
        self.user_model = ""
        self.actions = deque()
        self.model_score = 0

    # Print the current C2STEM model state
    def print_model_state(self):
        """
        Prints the current state of the C2STEMState instance.

        This method outputs the current C2STEM computational model.
        """
        print(f"Current User Model:\n{self.user_model}")

    # Print user actions
    def print_actions(self):
        """
        Prints the list of actions taken by the student in the C2STEM environment.

        This method outputs all actions recorded in the `actions` list.
        """
        print("Actions taken by the student:")
        for action in self.actions:
            print(action)