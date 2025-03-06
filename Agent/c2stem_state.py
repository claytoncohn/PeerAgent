class C2STEMState:
    """
    Manages the state for the agent server.

    This class provides functionality to maintain and update the state 
    of the server, including actions, user model, and WebSocket connections.
    It acts as a central repository for managing client interactions and 
    their respective states.
    """
    def __init__(self):
        """
        Initializes a new C2STEMState instance.

        Attributes
        ----------
        actions : list of str
            A list to store actions received from the client.
        user_model : str
            The current user model received from the client.
        socket : object
            The WebSocket connection associated with the client.
        """
        self.actions = []
        self.user_model = ""
        self.socket = ''

    # Add actions to state
    def add_actions(self, action: str):
        """
        Adds a new action to the state.

        Parameters
        ----------
        action : str
            The action string to be added to the list of actions.
        """
        self.actions.append(action)

    # Get actions from state
    def get_actions(self):
        """
        Retrieves all stored actions.

        Returns
        -------
        list of str
            The list of actions stored in the state.
        """
        return self.actions

    # Set user model received from state
    def set_user_model(self, model: str):
        """
        Updates the user model in the state.

        This method sets the `user_model` to the new value while preserving
        the current model as `prev_model`.

        Parameters
        ----------
        model : str
            The new user model to update the state with.
        """
        self.prev_model = self.user_model
        self.user_model = model

    # Get user model from state
    def get_user_model(self):
        """
        Retrieves the current user model.

        Returns
        -------
        str
            The current user model stored in the state.
        """
        return self.user_model

    # Set Socket for global use
    def set_socket(self, socket):
        """
        Assigns a WebSocket connection to the state.

        Parameters
        ----------
        socket : object
            The WebSocket connection object to associate with the client.
        """
        self.socket = socket

    # Get socket from state
    def get_socket(self):
        """
        Retrieves the assigned WebSocket connection.

        Returns
        -------
        object
            The WebSocket connection object stored in the state.
        """
        return self.socket