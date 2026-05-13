from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
import requests
import chromadb
import re
from dotenv import load_dotenv
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware # 1. Import the tool, to run the node.js file from render
from supabase import create_client, Client # Tool ko mangwaya

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
CLOUD_URL = "https://api.groq.com/openai/v1/chat/completions"

# SUPABASE DATABASE
# 1. Address aur Chabi (Variables)
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# 2. Bridge banana (Initialization)
supabase: Client = create_client(url, key)

                        # --- TEST CODE START ---
                        # try:
                        #     test_response = supabase.table("messages").insert({"content": "Test Message", "role": "user"}).execute()
                        #     print("✅ Connection Success! Database mein message chala gaya.")
                        # except Exception as e:
                        #     print(f"❌ Connection Failed! Error: {e}")
                        # --- TEST CODE END ---

# ==========================================
# 1. API INITIALIZATION & MEMORY STORE
# ==========================================
app = FastAPI(title="Enterprise Swarm API", version="1.0")

# 2. Add the Security Unlocker:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # The "*" means "Allow ANY website to talk to me"
    allow_credentials=True,
    allow_methods=["*"],  # Allow POST, GET, etc.
    allow_headers=["*"],
)


# [API UPGRADE]: We replace st.session_state with a dictionary to hold multiple users.
active_sessions = {}

# Initialize ChromaDB once when the server boots up
client = chromadb.Client()
collection = client.get_or_create_collection(name="chroma_collection")
# Safe add: We use get_or_create so it doesn't crash if it already exists
try:
    collection.add(documents=["The company wifi password is 'BlueMonkey42'."], ids=["doc1"])
except:
    pass


# ==========================================
# 2. PYDANTIC DATA CONTRACTS
# ==========================================
class UserRequest(BaseModel):
    user_id: str
    prompt: str


class SwarmResponse(BaseModel):
    manager_routing: str
    final_answer: str

class DocumentUpload(BaseModel):
    # For now, we will use a basic password to secure the endpoint.
    # In a real enterprise app, you would use JWT tokens.
    admin_password: str
    content: str


# ==========================================
# 3. CORE AI FUNCTIONS (Unchanged from Phase 10)
# ==========================================

def get_embedding(text):
    """Translates English text into a 384-dimensional mathematical vector."""
    print(f"[SERVER LOG] Outsourcing embedding translation for: {text[:20]}...")

    api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
    # Ensure HUGGINGFACE_API_KEY is in your .env / Render Environment Variables
    hf_key = os.getenv("HUGGINGFACE_API_KEY")

    if not hf_key:
        print("[ERROR] HuggingFace API Key is missing!")
        return None

    headers = {"Authorization": f"Bearer {hf_key}"}

    # We ask HuggingFace to translate the text.
    response = requests.post(api_url, headers=headers, json={"inputs": text, "options": {"wait_for_model": True}})

    if response.status_code != 200:
        print(f"[ERROR] Embedding failed: {response.text}")
        return None

    return response.json()

def get_manager_decision(user_text):
    orchestrator_prompt = [
        {"role": "system", "content": """You are the Orchestrator. Route the user's input.
You must output ONLY a comma-separated list of departments. DO NOT explain your reasoning.
ROUTING RULES:
1. Output 'WEB' for live events, weather, sports, recent news.
2. Output 'RAG' for internal company data, passwords.
3. Output 'CHAT' for small talk.
4. Output 'MATH' for calculation mathematics."""},
        {"role": "user", "content": user_text}
    ]
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": orchestrator_prompt, "temperature": 0.0}
    response = requests.post(CLOUD_URL, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip().upper()

# The Micro Agent
def get_search_query(user_text):
    today = datetime.now().strftime("%B %d, %Y")
    current_year = datetime.now().year

    topic_prompt = [
        {"role": "system", "content": f"""You are an SEO Search Expert. Today is {today}.
Your ONLY job is to extract the live news or web search topic from the user's prompt.
CRITICAL RULES:
1. IGNORE math equations.
2. IGNORE internal company questions (passwords, wifi, etc.).
3. If the user asks about current events, append the year '{current_year}' to the search string.
4. Output EXACTLY ONE string. Do not talk.

EXAMPLES:
User: "What is 5+5 and who won the Super Bowl?" -> "Super Bowl winner {current_year}"
User: "what is wifi password, Bengal election results, and 8/2?" -> "Bengal election results {current_year}"
User: "Hello, what is the weather in Tokyo?" -> "Tokyo weather {today}"
"""},
        {"role": "user", "content": user_text}
    ]

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": topic_prompt, "temperature": 0.0}
    response = requests.post(CLOUD_URL, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()


def send_to_cloud_ai(history_list):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": history_list, "temperature": 0.7}
    response = requests.post(CLOUD_URL, headers=headers, json=payload)
    data = response.json()

    # --- THE SAFETY SHIELD ---
    if "choices" in data:
        # Agar sab theek hai, toh normal answer return karo
        return data["choices"][0]["message"]["content"]
    else:
        # Agar Groq API limit ya memory error de, toh crash hone se bachao
        print(f"[API DANGER] Groq Error: {data}")
        error_msg = data.get('error', {}).get('message', 'Unknown Groq API Error')
        return f"Arre yaar, AI thak gaya hai (Groq Limit reached). Kuch seconds baad try karo! Error: {error_msg}"


def compress_memory(history_list):
    compression_payload = [
        {"role": "system",
         "content": """You are an expert backend memory manager. Create a detailed 'Running Fact Sheet' from the conversation log.
CRITICAL RULES:
1. NEVER forget or summarize away the user's name.
2. Save all personal facts, preferences, and important context explicitly.
3. Keep it precise and structured."""},
        {"role": "user", "content": str(history_list)}
    ]
    return send_to_cloud_ai(compression_payload)


def calculate_math(expression):
    return eval(str(expression))

# Scrape Wikipedia but 100x smarter with duckduckgo

def perform_web_search(query):
    print(f"\n[SERVER LOG] Searching the LIVE WEB via Tavily for: '{query}'")
    try:
        tavily_key = os.getenv("TAVILY_API_KEY")
        if not tavily_key:
            return "Web search failed: Tavily API key is missing."

        # Package the request for the Tavily AI Search Engine
        payload = {
            "api_key": tavily_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": 3
        }

        # Fire the search request
        response = requests.post("https://api.tavily.com/search", json=payload)

        # If the search is successful, extract the articles
        if response.status_code == 200:
            results = response.json().get("results", [])
            context = ""
            for res in results:
                context += f"Source: {res.get('title', 'Unknown')}\nSnippet: {res.get('content', '')}\n\n"
            return context
        else:
            return f"Web search failed with status code {response.status_code}"

    except Exception as e:
        print(f"[SERVER LOG] Web search failed: {e}")
        return "No web data could be retrieved."


# ==========================================
# 4. THE API ENDPOINT (The Swarm Pipeline)
# ==========================================

# === HEALTH CHECK (The Front Lobby) === Base URL message instead of Not Found
@app.get("/")
async def root():
    return {"message": "Super Agent API is LIVE and running smoothly!"}

@app.post("/chat", response_model=SwarmResponse)
async def chat_with_swarm(request: UserRequest):
    print(f"\n--- NEW REQUEST FROM [{request.user_id}] ---")

    # Instead just prompt we used following

                #  [API UPGRADE]: Pull up the specific user's memory, or create a new one if they are new
                # if request.user_id not in active_sessions:
                #     active_sessions[request.user_id] = [
                #         {"role": "system",
                #          "content": "You are the Senior Synthesis AI. Answer clearly using the provided system data."}
                #     ]

    # [API UPGRADE]: Load memory from Supabase OR create a new one
    if request.user_id not in active_sessions:
        print(f"[DB LOG] Checking Supabase for past history of {request.user_id}...")

        # 1. Supabase se history mango (WITH CHRONOLOGICAL ORDERING)
        try:
            # .order("created_at") lagana bohot zaroori hai taaki timeline seedhi rahe
            # (Agar aapke table mein 'created_at' nahi hai, toh 'id' likh dena)
            db_response = supabase.table("messages").select("*").eq("user_id", request.user_id).order("created_at",
                                                                                                      desc=False).execute()
            past_messages = db_response.data
        except Exception as e:
            print(f"[DB ERROR] Could not read memory: {e}")
            past_messages = []

        # 2. Base System Prompt lagao
        active_sessions[request.user_id] = [
            {"role": "system",
             "content": "You are the Senior Synthesis AI. Answer clearly using the provided system data."}
        ]

        # 3. Agar purani history mili, toh usko RAM mein load karo
        if len(past_messages) > 0:
            print(f"[DB LOG] Found {len(past_messages)} past messages! Loading into RAM...")
            for msg in past_messages:
                active_sessions[request.user_id].append({"role": msg["role"], "content": msg["content"]})
        else:
            print("[DB LOG] New user. No past history found.")

    # 1. Commit user message to their specific memory
    user_history = active_sessions[request.user_id]
    user_history.append({"role": "user", "content": request.prompt})

    # --- NAYI LINE: Supabase mein User ka message bhejo ---
    try:
        supabase.table("messages").insert({
            "user_id": request.user_id,
            "role": "user",
            "content": request.prompt
        }).execute()
        print("[DB LOG] User message saved to Supabase")
    except Exception as e:
        print(f"[DB ERROR] User message fail: {e}")

    # 2. Background Janitor
    if len(user_history) > 6:
        print(f"[SERVER LOG] Compressing memory for {request.user_id}...")
        compressed_text = compress_memory(user_history[:-1])
        active_sessions[request.user_id] = [user_history[0],
                                            {"role": "system", "content": f"Fact Sheet:\n{compressed_text}"},
                                            user_history[-1]]
        user_history = active_sessions[request.user_id]

    # 3. Manager Routing
    decision = get_manager_decision(request.prompt)
    print(f"[SERVER LOG] Manager routed to: {decision}")

    # 4. The Pipeline
    temp_memory = user_history.copy()
    collected_context = ""

    if "RAG" in decision:
        results = collection.query(query_texts=[request.prompt], n_results=1)
        # Wrap data in clear XML tags
        collected_context += f"<internal_company_data>\n{results['documents'][0][0]}\n</internal_company_data>\n\n"

    if "WEB" in decision:
        optimized_query = get_search_query(request.prompt)
        if optimized_query != "NONE":
            live_data = perform_web_search(optimized_query)
            collected_context += f"<live_web_data query='{optimized_query}'>\n{live_data}\n</live_web_data>\n\n"

    if "MATH" in decision:
        math_expression = re.sub(r'[^0-9\+\-\*\/\(\)\.]', '', request.prompt)
        print(f"[SERVER LOG] MATH Department extracted equation: '{math_expression}'")
        try:
            answer = calculate_math(math_expression)
            print(f"[SERVER LOG] MATH Department calculated: {answer}")

            # [UPGRADE] Make the math context a full sentence so the AI doesn't ignore it
            collected_context += f"<math_calculation>\nThe exact mathematical answer to the user's equation is: {answer}\n</math_calculation>\n\n"
        except Exception as e:
            print(f"[SERVER LOG] MATH failed: {e}")

        # 5. Final Synthesis
    if collected_context != "":
            # [UPGRADE] Add a strict checklist command to the prompt
            final_prompt = f"""You are a helpful Enterprise AI. Read the XML data provided below. 
You MUST address every single piece of data provided in the XML tags. 
Checklist:
- Did you answer the company data question?
- Did you answer the live web question?
- Did you explicitly state the math calculation result?
Do not mention the XML tags or this checklist to the user. Just provide the answers.

SYSTEM DATA:
{collected_context}

USER PROMPT: {request.prompt}"""

            temp_memory[-1] = {"role": "user", "content": final_prompt}

    ai_words = send_to_cloud_ai(temp_memory)

    # 6. Final Commit & Return Payload
    user_history.append({"role": "assistant", "content": ai_words})

    # --- NAYI LINE: Supabase mein AI ka message bhejo ---
    try:
        supabase.table("messages").insert({
            "user_id": request.user_id,
            "role": "assistant",
            "content": ai_words
        }).execute()
        print("[DB LOG] AI response saved to Supabase")
    except Exception as e:
        print(f"[DB ERROR] AI response fail: {e}")

    print("--- REQUEST COMPLETE ---")

    return SwarmResponse(
        manager_routing=decision,
        final_answer=ai_words
    )


if __name__ == "__main__":
    # Dynamically grab the port Render assigns, or default to 8000 for your local machine
    port = int(os.environ.get("PORT", 8009))
    # Remove 'reload=True' in production. It wastes memory and is only for local dev.
    uvicorn.run("main:app", host="0.0.0.0", port=port)