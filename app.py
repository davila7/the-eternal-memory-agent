import streamlit as st
import time
import os
import json
from judini.codegpt.chat import Completion
from judini.codegpt.agent import Agent
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from judini.codegpt.document import Document
from dotenv import load_dotenv
load_dotenv()

api_key= os.getenv("CODEGPT_API_KEY")
agent_id= os.getenv("CODEGPT_AGENT_ID")
st.set_page_config(layout="centered")

st.title("The Eternal Memory Agent 🧠")
st.markdown('---')
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("En que te puedo ayudar?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # obtener la última respuesta del assistant y la última pregunta del user
    last_assistant_message = ""
    last_user_message = ""

    # Search from the end to find the most recent messages
    for m in reversed(st.session_state.messages):
        if m["role"] == "assistant" and not last_assistant_message:
            last_assistant_message = m["content"]
        if m["role"] == "user" and not last_user_message:
            last_user_message = m["content"]
        # Stop searching once you have found the latest messages from both the user and the assistant
        if last_assistant_message and last_user_message:
            break

    # st.write('Last assistant message: ', last_assistant_message)
    # st.write('Last user message: ', last_user_message)
    # GPT-3.5-instruct to razoning if it's memorable
    is_memorable = False
    prompt_memorable = f'''
    User: {last_user_message}
    Chatbot: {last_assistant_message}

    [Selective Memory Consideration...]

    1. Does the ongoing substantive conversation contain emotionally impactful or particularly positive/negative content?
    2. Is there crucial information in the ongoing conversation that significantly affects the user or the current context?
    3. Was a complex or critical question posed in the ongoing conversation that requires further analysis?
    4. Is the ongoing conversation part of a key theme or critical discussion?
    5. Are there unique or exceptionally memorable details in the ongoing conversation that stand out?
    6. IMPORTANT: `is_memorable` must be False if the user gives their name as part of a standard self-introduction.

    Evaluate these aspects, explicitly excluding generic greetings, salutations, or language specifics, and decide whether the ongoing conversation is truly significant enough to remember.

    [Example]
    ###
    User: "I just received great news!"
    Chatbot: "That's wonderful! What's the good news?"
    Response: {{"is_memorable": "false", is_selfintroduction: "false", "reason": "User is indicating that he received good news but he is not telling the specific fact."}}
    ###
    ###
    User: "Hello, my name is Daniel."
    Chatbot: "Nice to meet you, Daniel! How can I assist you today?"
    Response: {{"is_memorable": "false", is_selfintroduction: "true", "reason": "It is a self-introduction"}}
    ###
    ###
    User: "During my last trip to Japan, I visited Kyoto and was amazed by the historic temples and beautiful gardens."
    Chatbot: "Japan sounds incredible! Which temple left the strongest impression on you?"
    Response: {{"is_memorable": "true", is_selfintroduction: "false", "reason": "the conversation contains information about the user's travel experiences."}}
    ###
    ###
    User: "I recently published a research paper on renewable energy technologies."
    Chatbot: "Congratulations on the publication! What specific aspect of renewable energy did you focus on?"
    Response: {{"is_memorable": "true", is_selfintroduction: "false", "reason": "the conversation contains information about the user's professional achievements."}}
    ###
    ###
    User: "I've recently taken up running to improve my cardiovascular health."
    Chatbot: "That's a great initiative! How has your experience with running been so far?"
    Response: {{"is_memorable": "true", is_selfintroduction: "false", "reason": "the conversation contains information about the user's health and fitness goals."}}
    ###


    Response: {{"is_memorable": "true or false", is_selfintroduction: "true or false", "reason": "Provide reason if memorable"}}
    '''
    #st.write(prompt_memorable)
    with st.status("Checking if it should be memorable..."):
        is_memorable_predict = ChatOpenAI(model_name="gpt-4")
        object_str = is_memorable_predict.predict(prompt_memorable)
        clean_object_str = object_str.replace('Response:', '').strip()
        # st.write(clean_object_str)
        # Convertir el objeto string JSON en un objeto Python
        object = json.loads(clean_object_str)
        is_memorable = object["is_memorable"]
        is_selfintroduction = object["is_selfintroduction"]
        reason = object["reason"]
        st.write("It's memorable: ",is_memorable)
        st.write("It's selft introduction: ", is_selfintroduction)
        st.write("Reason: ", reason)

        # Obtener los valores del objeto
        if(is_memorable == True):
            st.write('Keeping this memory...')
            # pasar pregunta y respuesta a embedding y obtener el document_id
            document_id = ""
            # asignar el documento al agente
            #updated = Agent(api_key).linkDocument(agent_id, document_id)

    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner('Wait for it...'):
            message_placeholder = st.empty()
            full_response = ""

            completion = Completion(api_key)
            prompt = st.session_state.messages

            response_completion = completion.create(agent_id, prompt, stream=False)
            for response in response_completion:
                time.sleep(0.05)
                full_response += (response or "")
                message_placeholder.markdown(full_response + "▌")       
            message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    
