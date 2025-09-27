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

    strategies_map = {
        "DEPTH_FIRST_ENACTING": "Students are currently using the Depth First Enacting strategy, where they build or adjust several blocks in succession without running the code to visualize the object's motion. This approach—similar to coding without periodic testing—is ineffective because it makes debugging harder; students cannot easily identify where their errors occur.",
        "TINKERING": "Students are currently engaged in Tinkering, a systematic strategy where they make small edits to their computational models and intermittently test them to visualize the object's motion. This informed trial-and-error approach is effective because it helps students see how each change affects the motion.",
        "TOOL_USE": "Students are using the Graph and Table Tools to visualize how variables change over time. This is a desirable strategy because it shows they are focused on understanding why the objects move the way they do, rather than just trying to make the model work for its own sake through trial-and-error.",
        "RUN_REPEAT":"Students are repeatedly clicking the Green Flag to test their models and visualize the object's motion on screen without intervening changes. This is generally an ineffective strategy: either they are running the same model while expecting different results—similar to ignoring compiler or interpreter errors—or they are replaying to analyze motion that would be better examined with the Graph and Table Tools.",
        "DRAFTING": "Students are currently engaged in Drafting, dragging blocks onto the screen that are not yet connected to the runnable model. This is similar to commenting or creating placeholder code to integrate later. Drafting can be an effective way to organize ideas in code form, but it becomes problematic if students don't realize that changes to drafted code will not affect the object's motion."
    }

    task_contexts_map = {
        "initialization":"Students are initializing variables in the environment. They need to connect several blocks—speed limit, acceleration, velocity, position, and delta_t—to the [When Green Flag Clicked] block. The sequence should end with the [start_simulation] block, which triggers the simulation loop to run the blocks under [simulation_step].",
        "updating-variables-every-sim-step":"Students are updating variables at each simulation step. This requires correctly using 'change by' blocks (the equivalent of += in code) to update position and velocity at the start of each loop, based on the kinematic equations. A common mistake is confusing 'set' blocks—used for initialization—with 'change by' blocks—used for updating.",
        "conditional-clause":"Students are crafting conditional statements to control cruising, deceleration, and stopping. For cruising, they must check if the velocity is greater than the speed limit. For deceleration, they must use kinematic equations to calculate the lookahead distance and determine how far before the stop sign the truck should slow down. For stopping, the truck must have passed the stop sign and its velocity must be less than zero.",
        "updating-variables-under-conditons":"Students are updating variables within the conditional statements. For cruising, they must set acceleration to zero. For decelerating, they must set acceleration to -4. For stopping, they must stop the simulation."
    }

    def __init__(self):
        utc_now = datetime.datetime.now(pytz.utc)
        central_tz = pytz.timezone('America/Chicago')
        central_now = utc_now.astimezone(central_tz)
        formatted_time = central_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')

        self.user_model = ""
        self.raw_actions = deque()
        self.action_groups = deque()
        self.model_scores = deque()
        self.task_contexts = deque()
        self.strategies = deque()

        self.learner_state = deque()
        self.learner_state.append({"time":formatted_time,"summary":"Initial learner state.","learner_state":"STARTING"})

        self.needed_domain_knowledge = deque()
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