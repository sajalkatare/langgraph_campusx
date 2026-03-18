import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

## Basic Streamlit app to demonstrate chat interface ##

# with st.chat_message("user"):
#     st.write("Hello, how are you?")

# with st.chat_message("assistant"):
#     st.write("I'm doing well, thank you! How can I assist you today?")

# with st.chat_message("user"):
#     st.write("My Name is BabaYaga.")

# user_input = st.chat_input("Type your message here...")

# if user_input:
#     with st.chat_message("user"):
#         st.write(user_input)

##################################################################

# user_input = st.chat_input("Type your message here...")

# if user_input:
#     with st.chat_message("user"):
#         st.write(user_input)

#     # We will show same message as assistant for demonstration, you can replace it with actual response from your chatbot
#     with st.chat_message("assistant"):
#         st.write(user_input)

# In Above code when you type and send a message old messge will get replace because we are not saving the conversation history. To save the conversation history we can use session state in streamlit.

#####################################################################

# st.session_state -> dict -> 




CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])



user_input = st.chat_input('Type here')

if user_input:

    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    response = chatbot.invoke({'messages': [HumanMessage(content=user_input)]}, config=CONFIG)
    
    ai_message = response['messages'][-1].content
    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        st.text(ai_message)