# ============================================================
# Import required libraries
# ============================================================

import streamlit as st  # Streamlit is used to build the web UI of the chatbot app
from langgraph_backend import chatbot  # Our custom chatbot logic powered by LangGraph (handles AI responses)
from langchain_core.messages import HumanMessage, AIMessage  # Message types: HumanMessage = user, AIMessage = AI/bot
import uuid  # Used to generate unique IDs for each chat conversation/thread


# ======================================== Utility Functions =========================
# These are helper functions used throughout the app


def generate_thread_id():
    """
    Creates a brand-new unique ID for a chat session.
    Every time you start a new conversation, it gets its own unique thread_id
    so the chatbot can keep track of different conversations separately.
    """
    thread_id = uuid.uuid4()  # uuid4() generates a random unique ID (e.g., 'a3f5c2d1-...')
    return thread_id


def reset_chat():
    """
    Starts a completely fresh chat conversation.
    - Generates a new unique thread ID
    - Saves it to the session
    - Registers it in the list of all threads
    - Clears the visible chat message history on screen
    """
    thread_id = generate_thread_id()                    # Step 1: Create a new unique thread ID
    st.session_state['thread_id'] = thread_id          # Step 2: Set it as the active/current thread
    add_thread(st.session_state['thread_id'])          # Step 3: Add this new thread to our conversation list
    st.session_state['message_history'] = []           # Step 4: Clear the chat screen (empty message list)


def add_thread(thread_id):
    """
    Adds a thread ID to our list of saved conversations (if not already there).
    This ensures we don't add duplicate threads to the sidebar list.
    """
    if thread_id not in st.session_state['chat_threads']:  # Only add if it's a new thread
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    """
    Fetches the full message history of a previous conversation from LangGraph's memory.
    LangGraph saves the state (messages) of each thread, so we can reload old chats.
    Returns an empty list if no messages are found for that thread.
    """
    # Ask the chatbot backend for the saved state of the given thread
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})

    # Extract messages from the state; return [] if there are no messages yet
    return state.values.get('messages', [])


# ======================================== Session Setup ==============================
# Streamlit reruns the entire script on every interaction.
# st.session_state acts like a memory that persists across these reruns.
# Here we initialize the required state variables only if they don't already exist.

if 'message_history' not in st.session_state:
    # Stores the list of chat messages shown on screen
    # Format: [{'role': 'user' or 'assistant', 'content': 'message text'}, ...]
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    # Each chat session has a unique thread ID so the AI can remember the conversation context
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    # Keeps track of all conversation thread IDs so we can list them in the sidebar
    st.session_state['chat_threads'] = []

# Register the current thread in the thread list (in case it's a fresh app load)
add_thread(st.session_state['thread_id'])


# ======================================== Sidebar UI =================================
# The sidebar shows the chatbot title, a "New Chat" button, and past conversations


st.sidebar.title('LangGraph Chatbot')  # App title shown at the top of the sidebar

# "New Chat" button — clicking this resets everything and starts a fresh conversation
if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')  # Section header for listing past chats

# Loop through all saved thread IDs and show each as a clickable button in the sidebar
# [::-1] reverses the list so the most recent conversation appears at the top
for thread_id in st.session_state['chat_threads'][::-1]:

    # Each thread ID becomes a clickable button labeled with its unique ID
    if st.sidebar.button(str(thread_id)):

        # When clicked, switch the active thread to the selected one
        st.session_state['thread_id'] = thread_id

        # Load the full message history for this thread from LangGraph's memory
        messages = load_conversation(thread_id)

        # Convert LangGraph message objects into the simple dict format our UI uses
        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'        # Messages from the user
            else:
                role = 'assistant'   # Messages from the AI bot

            # Append the converted message to our temp list
            temp_messages.append({'role': role, 'content': msg.content})

        # Replace the current on-screen chat history with the loaded conversation
        st.session_state['message_history'] = temp_messages


# ======================================== Main Chat UI ============================
# This is the central area where the conversation is displayed and user can type


# Replay all previously saved messages so the chat history is visible on screen
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):  # Displays with correct avatar: user or assistant
        st.text(message['content'])         # Show the text content of each message


# Chat input box fixed at the bottom of the screen — waits for user to type
user_input = st.chat_input('Type here')

# This block runs only when the user has typed something and hit Enter
if user_input:

    # --- Display and save the user's message ---
    # Add user's message to the session history so it persists across reruns
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})

    # Immediately show the user's message in the chat UI with user avatar
    with st.chat_message('user'):
        st.text(user_input)

    # --- Build the config for this chat thread ---
    # The thread_id tells LangGraph which conversation's memory to use
    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # --- Stream and display the AI's response ---
    with st.chat_message("assistant"):  # Show response under the assistant avatar

        def ai_only_stream():
            """
            A generator function that streams the AI's response token by token.
            - Sends the user's message to the LangGraph chatbot
            - Listens to streamed message chunks as they arrive
            - Only yields text from AIMessage chunks (ignores tool calls, metadata, etc.)
            This makes the response appear gradually (typewriter effect) instead of all at once.
            """
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},  # Send user's input to the chatbot
                config=CONFIG,                                      # Use the current thread's config
                stream_mode="messages"                             # Stream individual message tokens
            ):
                if isinstance(message_chunk, AIMessage):   # Filter: only process AI response chunks
                    yield message_chunk.content             # Yield each token so it streams to the UI

        # st.write_stream() calls our generator and renders each yielded token live on screen
        # It also returns the full assembled response string once streaming is complete
        ai_message = st.write_stream(ai_only_stream())

    # --- Save the AI's full response to session history ---
    # After streaming is done, save the complete AI response for future reruns
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})