#!/usr/bin/env python3
import json
import logging
from openai import OpenAI
from xai_module import XAI_module

# Configure logging (optional)
logging.basicConfig(level=logging.INFO)

# Replace with your actual OpenAI API key

client = OpenAI(api_key="API_KEY_HERE")

def get_openai_response(prompt):
    """
    Helper function to call the OpenAI API using the new client method.
    It takes a list of messages (prompt) and returns the assistant's reply text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or your preferred model
            messages=prompt,
            temperature=0.2,      # Lower temperature for more deterministic responses
        )
        # Access the content using the new attribute notation
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return "{}"  # Return an empty JSON string on error

def print_help():
    print("\nAvailable commands:")
    print("  /help         - Show this help message")
    print("  /state        - Display the current knowledge state")
    print("  /explain      - Display suggested explanations for missing concepts")
    print("  /clear        - Clear the conversation history")
    print("  /exit         - Exit the CLI\n")
    print("  /update_state - Update the student's knowledge state based on the current conversation history")
    print("  /summary      - Display the current summary of the knowledge state\n")

def main():
    print("Welcome to the XAI Module CLI demo.")
    print("Please input the problem description:")
    print("or type '/demo' to use a sample problem and editorial.")
    problem_description = input("Problem: ")
    if problem_description == "/demo":
        # use demo_problem.txt and demo_editorial.txt
        with open("./Agent/demo_problem.txt", "r", encoding='utf-8') as file:
            problem_description = file.read()
        with open("./Agent/demo_editorial.txt", "r", encoding='utf-8') as file:
            editorial_solution = file.read()
        print("\nUsing the sample problem and editorial.")
    else:
        print("\nPlease input the editorial solution:")
        editorial_solution = input("Editorial: ")

    # Create an instance of XAI_module with the provided problem and editorial.
    xai = XAI_module(problem_description, editorial_solution)

    # Analyze the problem to extract educational concepts and initialize the knowledge state.
    xai._analyze_problem(problem_description, editorial_solution, get_openai_response)
    print("\nExtracted Concepts:", xai.concepts)
    print("Initial Knowledge State:", json.dumps(xai.get_knowledge_state(), indent=4))

    # Initialize conversation history as a list of message dictionaries.
    conversation = []
    print("\nYou can now start a conversation (type '/help' for available commands).")

    while True:
        user_input = input(">> ").strip()
        if user_input.startswith("/"):
            # Process CLI commands
            if user_input == "/help":
                print_help()
            elif user_input == "/state":
                print("\nCurrent Knowledge State:")
                print(json.dumps(xai.get_knowledge_state(), indent=4))
            elif user_input == "/summary":
                print("\nSummary:")
                print(xai.summary)
            elif user_input == "/explain":
                explanations, reasoning = xai.suggest_explanations(conversation, get_openai_response)
                print("\nSuggested Explanations:")
                print(json.dumps(explanations, indent=4))
                print("CoT:")
                print(reasoning)
            elif user_input == "/clear":
                conversation = []
                print("\nConversation history cleared.")
            elif user_input == "/exit":
                print("\nExiting CLI. Goodbye!")
                break
            elif user_input =="/update_state":
                # Update the student's knowledge state based on the current conversation history.
                xai.analyze_messages(conversation, get_openai_response)
            else:
                print("\nUnknown command. Type '/help' for a list of commands.")
        else:
            # Treat input as a student message.
            student_message = {"role": "user", "content": user_input}
            conversation.append(student_message)

            # Build the assistant prompt using the full conversation history:
            assistant_prompt = [{"role": "system", "content": "You are a helpful educational assistant."}] + conversation

            # Get a response using the entire context.
            assistant_response = get_openai_response(assistant_prompt)
            assistant_message = {"role": "assistant", "content": assistant_response}
            conversation.append(assistant_message)
            print("\nAssistant:", assistant_response)


if __name__ == "__main__":
    main()
