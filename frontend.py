import streamlit as st
import requests
import uuid

# === 1. UI CONFIGURATION ===
st.set_page_config(page_title="Enterprise Swarm", page_icon="🐝")
st.title("🐝 Enterprise AI Swarm")

# === 2. API CONNECTION (THE BRIDGE) ===
# [IMPORTANT]: Paste your actual Render URL here. Make sure it ends in /chat!
API_URL = "https://super-agent-0ycr.onrender.com/chat"

# === 3. SESSION MEMORY ===
# We need to give this specific browser window a unique ID so the API remembers who we are.
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())  # Generates a random string like '123e4567-e89b-12d3...'

# We need to store the chat history just for the visual screen
if "messages" not in st.session_state:
    st.session_state.messages = []

# === 4. DRAW THE CHAT HISTORY ===
# This loops through all past messages and draws them on the screen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === 5. THE USER INPUT BOX ===
# This creates the text box at the bottom of the screen
if prompt := st.chat_input("Ask the Swarm a question..."):

    # A. Instantly draw the user's message on the screen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # B. Send the package to the Cloud API
    with st.chat_message("assistant"):
        with st.spinner("The Swarm is thinking..."):  # Shows a loading spinner

            # Package the data exactly how Pydantic expects it
            payload = {
                "user_id": st.session_state.session_id,
                "prompt": prompt
            }

            try:
                # Fire the package over the internet to Render!
                response = requests.post(API_URL, json=payload)

                if response.status_code == 200:  # 200 means "OK / Success"
                    data = response.json()
                    answer = data["final_answer"]
                    routing = data["manager_routing"]

                    # Draw the AI's final answer
                    st.markdown(answer)

                    # Draw a cool badge showing which departments the Manager used
                    st.caption(f"🛣️ *System routed via: {routing}*")

                    # Save the AI's answer to the visual history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"API Error: {response.status_code}")

            except Exception as e:
                st.error(f"Failed to connect to the cloud API. Is the server awake? Error: {e}")