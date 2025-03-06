class LearnerModel:
    """
    Learner model of students using C2STEM. This tracks things like the students' computational model state and actions.
    The learner model will be used for dialogue management and guiding agent conversations to personalze student-agent interactions.

    Attributes
    ----------
    user_model : str
        A string representing the students' current computational model in C2STEM.

    Methods
    -------
    None
    """
    def __init__(self):
        self.user_model = ""