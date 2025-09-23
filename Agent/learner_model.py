from collections import deque
from globals import Config
import datetime
import pytz

class LearnerModel:
    """
    Learner model of students using C2STEM. This tracks things like the students' computational model state and actions.
    The learner model will be used for dialogue management and guiding agent conversations to personalze student-agent interactions.

    Attributes
    ----------
    user_model : str
        A string representing the students' current computational model in C2STEM.
    raw_actions : deque
        A deque of the actions taken by the student in the C2STEM environment. 
        Each action is represented as a dictionary with keys "time", "type", and "block".
    action_groups : deque
        A deque of the action groups taken by the student with keys "time" and "action".
    model_scores: deque
        A deque of the model scores with keys "time" and "scores", where "scores" is a dictionary of individual scores and a "total_score".
    task_contexts: deque
        A deque of the task contexts with keys "time" and "segment", where "segment" is a string representing the current task segment.
    strategies: deque
        A deque of strategies used by the student with keys "time" and "strategy", where "strategy" is a string representing the strategy used.
    
    Methods
    -------
    print_model_state()
        Prints the current state of the C2STEM model.
    print_raw_actions()
        Prints the list of the last N actions (defined in .env) taken by the student in the C2STEM environment.
    stringify_action_groups()
        Converts the action groups to a string representation.
    """

    def __init__(self):
        self.user_model = ""
        self.raw_actions = deque()
        self.action_groups = deque()
        self.model_scores = deque()
        self.task_contexts = deque()
        self.strategies = deque()
        self.needed_domain_knowledge = deque()

        utc_now = datetime.datetime.now(pytz.utc)
        central_tz = pytz.timezone('America/Chicago')
        central_now = utc_now.astimezone(central_tz)
        formatted_time = central_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        self.needed_domain_knowledge.append({"time":formatted_time,"summary":"Initial domain knowledge needed.","recommended_domain_knowledge":"Students should start by initializing variables","knowledge":"Students must begin by initializing variables under the [When Green Flag Clicked] block."})

    # Print the current C2STEM model state
    def print_model_state(self):
        """
        Prints the current state of the C2STEMState instance.

        This method outputs the current C2STEM computational model.
        """
        print(f"Current User Model:\n{self.user_model}")

    # Print user actions
    def print_raw_actions(self):
        """
        Prints the list of actions taken by the student in the C2STEM environment.

        This method outputs all actions recorded in the `raw_actions` deque.
        """
        print("Actions taken by the student:")
        for action in self.raw_actions:
            print(action)

    def stringify_action_groups(self):
        """
        Converts the action groups to a string representation.

        This method concatenates the string representations of all action groups
        in the `action_groups` deque, separated by newlines.

        Returns
        -------
        str
            A string representation of all action groups.
        """
        return "\n".join(str(group["action"]) for group in self.action_groups)