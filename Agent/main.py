from c2stem_action import C2STEMAction
import time

from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from agent import Agent  # Ensure agent.py is in the same folder
import uvicorn
from globals import Config
import json
from c2stem_state import C2STEMState
import logging
import threading
import asyncio
import gradio.queueing as queueing
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
This is the entry file to the agent server implementation. 
The python file sets up the websocket connection and the user state for maintenance.
The file sends the chat window url on initialization to the front end.
The file listens to the messages on websocket and saves them to userState.
"""

#  Global variables and data structure
# chat_window_URL = "URL= http://127.0.0.1:7860",
chat_window_URL = "URL= https://agent.c2-stem.org",
# computational_model_state = C2STEMState()
user_computational_models: Dict[str, C2STEMState] = {}
agent = Agent(use_gui=True)

original_init = queueing.Queue.__init__

def new_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    # Replace the pending_message_lock with an asyncio.Lock if it isn’t already one.
    self.pending_message_lock = asyncio.Lock()
    self.delete_lock = asyncio.Lock()

queueing.Queue.__init__ = new_init


def run_agent_initialization():
    """
    Runs the agent initialization in a separate thread with its own event loop.
    This prevents the RuntimeWarning about unawaited coroutines.
    """

    async def initialize_agent_server():
        """
        Initializes the agent server.

        This function initializes the WebSocket connection for the agent server.
        It invokes the agent's talk method. It also handles exceptions during initialization.

        This class also handles students' computational model state and actions, updating the learner model accordingly.

        Raises
        ------
        Exception
            If an error occurs while sending the URL or initializing the agent server.
        """
        try:
            agent.start_strategy_generation()
            agent.start_domain_knowledge_retrieval()
            agent.talk()
        except Exception as e:
            logging.error(f"Error initializing agent server: {e}")

    # Create and run a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(initialize_agent_server())
    except Exception as e:
        logging.error(f"Error in agent initialization thread: {e}")
    finally:
        loop.close()


# Launch the GUI Agent on startup in a separate thread.
@app.on_event("startup")
async def startup_event():
    """
    Startup event handler that launches the agent initialization in a separate thread.
    """
    await asyncio.sleep(1)  # Give the main app a moment to start

    # Start the agent initialization in a separate thread
    agent_thread = threading.Thread(target=run_agent_initialization, daemon=True)
    agent_thread.start()
    logging.info("Agent initialization thread started")

# async def initialize_agent_server():
#     """
#     Initializes the agent server.
#
#     This function initializes the WebSocket connection for the agent server.
#     It invokes the agent's talk` method. It also handles exceptions during initialization.
#
#     This class also handles students' computational model state and actions, updating the learner model accordingly.
#
#     Raises
#     ------
#     Exception
#         If an error occurs while sending the URL or initializing the agent server.
#     """
#     agent.start_strategy_generation()
#     agent.start_domain_knowledge_retrieval()
#     agent.talk()
#
# # Launch the GUI Agent on startup in a separate thread.
# @app.on_event("startup")
# async def startup_event():
#     await asyncio.sleep(1)
#     threading.Thread(target=initialize_agent_server, daemon=True).start()

@app.post("/app/api/login")
async def login(username: str = Body(...), password: str = Body(...)):
    # Dummy authentication.
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    # In production, validate against your MongoDB users store.
    # return {"success": True, "username": username}
    resp = JSONResponse({"success": True, "username": username})
    # Domain must match where Gradio lives:
    resp.set_cookie(
        key="username",
        value=username,
        domain="agent.c2-stem.org",
        httponly=False,
        secure=True,
        samesite="none"
    )
    return resp

@app.post("/app/api/conversations")
async def get_conversations():
    data_dict = {}
    for filename in os.listdir(Config.convo_save_path):
        file_path = os.path.join(Config.convo_save_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                key = filename.split("_")[3]
                data_dict[key] = content
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load {filename}: {e}")

    return data_dict

@app.post("/app/api/conversations/{username}")
async def get_conversation(username):
    data_dict = {}
    for filename in os.listdir(Config.convo_save_path):
        if username in filename:
            file_path = os.path.join(Config.convo_save_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    key = filename.split("_")[3]
                    data_dict[key] = content
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: Could not load {filename}: {e}")

    return data_dict



# Message handler for incoming message over the WebSocket.
@app.websocket("/app/ws/data")
async def handler(websocket: WebSocket, username: str = Query(...)):
    """
    Handles incoming WebSocket messages and maintains the user state.

    This function manages communication over a WebSocket connection. It:
    1. Establishes a new connection and assigns it to the `user_state`.
    2. Sends chat window URL to the client.
    3. Initializes the agent server for the connection.
    4. Processes incoming messages, which may include actions, user state updates, 
       or other types, and appropriately updates the `user_state`.

    Parameters
    ----------
    websocket : websockets.WebSocketServerProtocol
        The WebSocket connection object generated by the server.

    Raises
    ------
    websockets.exceptions.ConnectionClosed
        If the WebSocket connection is closed unexpectedly.
    Exception
        For any general errors that occur during message handling.

    Notes
    -----
    - Incoming messages are expected to be JSON formatted.
    - Recognized message types are "action" and "state". Unrecognized types are 
      returned back to the sender.
    - Invalid JSON messages are handled gracefully, returning an error response.
    """
    try:
        if username not in user_computational_models:
            user_computational_models[username] = C2STEMState();
        computational_model_state = user_computational_models[username]
        # Assigning websocket to user state to be used globally.
        computational_model_state.set_socket(websocket)
        global chat_window_URL
        await websocket.accept()
        try:
            # Hardcoded chat_window_URL to http://127.0.0.1:7860, as this is Gradio default
            await websocket.send_text(chat_window_URL)
            logging.info("Chat window URL sent to client.")
        except Exception as e:
            logging.error(f"Error initializing agent server: {e}")
        logging.info("New Websocket connection established")

        # async for message in websocket:
        try:
            while True:
                # Parse the incoming message
                # message = json.loads(message)
                data = await websocket.receive_text()
                message = json.loads(data)

                time_now = int(time.time()*1000)

                # Process C2STEM physics actions
                if message['type'] == "action":
                    action = C2STEMAction(message['data'])
                    if action.action_type not in {"togglePause", "stopAllScripts", "toggleWatcher", "tableDialog", "graphDialog"}:
                        agent.learner_model.raw_actions.append(
                            {"time": time_now, "type": action.action_type, "block": action.block}
                        )
                        logging.info(f"Action added:\n{agent.learner_model.raw_actions[-1]}")

                # Update the user model
                elif message['type'] == "state":
                    new_state = str(message['data'])
                    if new_state != computational_model_state.user_model:
                        computational_model_state.set_user_model(new_state)
                        agent.learner_model.user_model = computational_model_state.user_model
                        logging.info(f"User model updated: {agent.learner_model.user_model}")

                elif message['type'] == "group":
                    agent.learner_model.action_groups.append({"time":time_now,"action":message['data']})
                    logging.info(f"User Action Group Updated: {agent.learner_model.action_groups[-1]['action']}")

                elif message['type'] == "score":
                    agent.learner_model.model_scores.append({"time":time_now,"scores":message['data']})
                    total_score_values = [v for k, v in message['data'].items() if k not in {"physics_mastery","computing_mastery","overall_mastery"}]
                    agent.learner_model.model_scores[-1]["scores"]["total_score"] = sum(total_score_values)
                    logging.info(f"User Action Score Updated: {agent.learner_model.model_scores[-1]['scores']['total_score']}")

                elif message['type'] == "segment":
                    agent.learner_model.task_contexts.append({"time":time_now,"segment":message['data']})
                    logging.info(f"User Task Context Updated: {message['data']}")
                else:
                    await websocket.send_text(message['data'])
        except json.JSONDecoderError:
            await websocket.send_text(json.dumps({"type": "error", "data": "Invalid JSON format."}))
            logging.error("Invalid message type received")
    except WebSocketDisconnect:
        logging.error("WebSocket connection closed.")
    except Exception as e:
        logging.error(f"Error in handler: {e}")

@app.get("/app")
def root():
    return {"msg": "Backend is running"}


if __name__ == "__main__":
    # For development, you might run: uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# def run_websocket_server():
#     """
#     Starts and runs a WebSocket server on a separate thread.
#
#     This function initializes and starts a WebSocket server that listens
#     on `ws://localhost:8080` using Python's `websockets` library.
#     The server runs indefinitely until a `KeyboardInterrupt` is received,
#     which gracefully shuts it down.
#
#     The function uses an asyncio event loop to manage the asynchronous
#     WebSocket server and runs it indefinitely.
#
#     Notes
#     -----
#     - The WebSocket server is designed to run on `ws://localhost:8080`.
#     - The `handler` function should be defined elsewhere to process incoming
#       WebSocket connections.
#     - Proper logging is used to record server startup and shutdown events.
#
#     Raises
#     ------
#     KeyboardInterrupt
#         If the server is interrupted manually, it shuts down gracefully.
#
#     """
#
#     async def websocket_server():
#         logging.info("Starting WebSocket server on ws://localhost:8080")
#         try:
#             # Start the WebSocket server and run it indefinitely
#             async with websockets.serve(handler, "localhost", 8080):
#                 logging.info("WebSocket server successfully started and listening on ws://localhost:8080")
#                 try:
#                     await asyncio.Future()  # run forever
#                 except KeyboardInterrupt:
#                     logging.info("Shutting down the WebSocket server")
#         except Exception as e:
#             logging.error(f"Failed to start WebSocket server: {e}")
#             raise
#
#     # Run the WebSocket server using asyncio's event loop
#     asyncio.run(websocket_server())
#
#
# async def main():
#     """
#     This function creates and starts a WebSocket server that listens on
#     `ws://localhost:8080` for incoming connections. It runs until manually
#     terminated or interrupted.
#
#     Raises
#     ------
#     KeyboardInterrupt
#         If the server is manually terminated using a keyboard interrupt.
#     """
#     try:
#         # Starts the WebSocket server in a separate thread.
#         websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
#         websocket_thread.start()  # Start the thread
#
#         # Give the WebSocket server a moment to start up
#         await asyncio.sleep(1)
#
#         # Run initialize_agent_server in the main thread
#         await initialize_agent_server()
#     except KeyboardInterrupt:
#         # Graceful exit on Ctrl+C
#         print("Program interrupted by user. Shutting down.")
#     except Exception as e:
#         # Handle unexpected errors
#         print(f"An unexpected error occurred: {e}")
#
#
# if __name__ == "__main__":
#     """
#     Entry point for the agent server script.
#
#     Based on the environment (`Config.env`), this script either:
#     1. Runs the `agent.talk` method in development mode.
#     2. Starts the WebSocket server in production mode.
#     3. Raises an exception if the environment is invalid.
#
#     Raises
#     ------
#     Exception
#         If `Config.env` is not set to "dev" or "prod".
#     """
#     if Config.env == "dev":
#         agent.talk()
#     elif Config.env == "prod":
#         try:
#             asyncio.run(main())
#         except Exception as e:
#             logging.error(f"Error running the server: {e}")
#     else:
#         raise Exception("Invalid environment. Must be 'dev' or 'prod'.")
