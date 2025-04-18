
import json
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from agent import Agent  # Ensure agent.py is in the same folder
import uvicorn
from globals import Config
import asyncio
# import websockets
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
    allow_origins=["*"],  # Change as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# user_agents: Dict[str, Agent] = {}
user_computational_models: Dict[str, C2STEMState] = {}

#  Global variables and data structure
# chat_window_URL = "URL= http://localhost:7860",
chat_window_URL = "URL= https://agent.c2-stem.org",
# computational_model_state = C2STEMState()
agent = Agent(use_gui=True)

original_init = queueing.Queue.__init__

def new_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    # Replace the pending_message_lock with an asyncio.Lock if it isn’t already one.
    self.pending_message_lock = asyncio.Lock()
    self.delete_lock = asyncio.Lock()

queueing.Queue.__init__ = new_init

def launch_agent():
    # This will call the built-in GUI (agent.talk) from agent.py.
    # Because _talk_with_gui now launches in non-blocking mode, this thread will finish
    # quickly after launching the Gradio server.
    agent.talk()


# Launch the GUI Agent on startup in a separate thread.
@app.on_event("startup")
async def startup_event():
    threading.Thread(target=launch_agent, daemon=True).start()


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
    # if username not in user_agents:
    #     # Create a new Agent instance without launching the Gradio GUI.
    #     user_agents[username] = Agent(use_gui=False)
    # agent = user_agents[username]
    # agent.talk()
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
                # user_message = data_json.get("message", "").strip()
                # Process C2STEM physics actions
                if message['type'] == "action":
                    pass  # Not using actions yet
                    # computational_model_state.add_actions(str(message['data']))
                    # logging.info(f"Action added: {message['data']}")

                # Update the user model
                elif message['type'] == "state":
                    computational_model_state.set_user_model(str(message['data']))
                    agent.learner_model.user_model = computational_model_state.user_model
                    logging.info(f"User model updated: {agent.learner_model.user_model}")

                else:
                    await websocket.send_text(message['data'])
        except json.JSONDecoderError:
            await websocket.send_text(json.dumps({"type": "error", "data": "Invalid JSON format."}))
            logging.error("Invalid message type received")
    except WebSocketDisconnect:
        print("User disconnected from chat.")
    except Exception as e:
        logging.error(f"Error in handler: {e}")


# launch_gradio()


@app.get("/app")
def root():
    return {"msg": "Backend is running"}


if __name__ == "__main__":
    # For development, you might run: uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)