import streamlit as st
import requests

# === 1. UI CONFIGURATION ===
st.set_page_config(page_title="Enterprise Swarm", page_icon="🐝", layout="wide")

# === 2. API CONNECTION (THE BRIDGE) ===
# We declare the base URL so we can route to both /chat and /upload-doc
BASE_API_URL = "https://swarm-api-super-agent-travily.onrender.com"

# === 3. SESSION MEMORY & IDENTITY ===
# Instead of a random UUID, we let you lock in a specific username.
if "username" not in st.session_state:
    st.session_state.username = "nayan_desktop"

# NEW THE FLAG: Tracks whose history we have currently downloaded
if "history_loaded_for" not in st.session_state:
    st.session_state.history_loaded_for = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# === 4. THE ADMIN VAULT (SIDEBAR) ===
with st.sidebar:
    st.header("⚙️ Admin Knowledge Vault")
    st.write("Securely upload rules, facts, or company data to the AI's Supabase brain.")

    upload_content = st.text_area("Document Content", height=150, placeholder="Type facts here...")

    # type="password" hides it with dots. Remove type="password" if you want to see the text!
    admin_password = st.text_input("Admin Password", type="password", placeholder="Enter secret...")

    if st.button("Upload to Brain", type="primary"):
        if not upload_content or not admin_password:
            st.error("⚠️ Missing content or password!")
        else:
            with st.spinner("Encrypting and Uploading..."):
                try:
                    response = requests.post(
                        f"{BASE_API_URL}/upload-doc",
                        json={
                            "admin_password": admin_password,
                            "user_id": st.session_state.username,
                            "content": upload_content
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.success("✅ Knowledge secured in vault!")
                        else:
                            st.error(f"❌ Failed: {result.get('message', 'Unauthorized')}")
                    else:
                        st.error(f"❌ Server rejected request. Status: {response.status_code}")
                except Exception as e:
                    st.error("🔌 Network error. Is Render awake?")

# === 5. MAIN CHAT UI ===
st.title("🐝 Enterprise AI Swarm")

# Give the user a way to change their ID to test memory
st.session_state.username = st.text_input("🔑 Your Memory ID (Keep this the same to retain memory):",
                                          value=st.session_state.username)

# Draw the chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === 6. THE USER INPUT BOX ===
if prompt := st.chat_input("Ask the Swarm a question..."):

    # Instantly draw the user's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Hit the Render API
    with st.chat_message("assistant"):
        with st.spinner("The Swarm is thinking..."):

            payload = {
                "user_id": st.session_state.username,  # Using your persistent ID here!
                "prompt": prompt
            }

            try:
                response = requests.post(f"{BASE_API_URL}/chat", json=payload)

                if response.status_code == 200:
                    data = response.json()
                    answer = data["final_answer"]
                    routing = data["manager_routing"]

                    st.markdown(answer)
                    st.caption(f"🛣️ *System routed via: {routing}*")

                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error(f"API Error: {response.status_code}")

            except Exception as e:
                st.error(f"Failed to connect to the cloud API. Error: {e}")