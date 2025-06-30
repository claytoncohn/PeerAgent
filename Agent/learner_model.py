class LearnerModel:
    """
    Learner model of students using C2STEM. This tracks things like the students' computational model state and actions.
    The learner model will be used for dialogue management and guiding agent conversations to personalze student-agent interactions.

    Attributes
    ----------
    user_model : str
        A string representing the students' current computational model in C2STEM.
    actions : list
        A list of actions taken by the student in the C2STEM environment.

    Methods
    -------
    print_model_state()
        Prints the current state of the C2STEM model.
    """
    def __init__(self):
        self.user_model = ""
        self.actions = []

        # Once scoring function is complete, will implement
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
            print(f"Time: {action.t}, Action Type: {action.action_type}, Block: {action.block}")