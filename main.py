from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import os
import requests
# import chromadb
import re
from dotenv import load_dotenv
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware # 1. Import the tool, to run the node.js file from render
from supabase import create_client, Client # Tool ko mangwaya
from huggingface_hub import InferenceClient

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

# used supabase rpc and hugging face for RAG, dont need chromaDB
        # # Initialize ChromaDB once when the server boots up
        # client = chromadb.Client()
        # collection = client.get_or_create_collection(name="chroma_collection")
        # # Safe add: We use get_or_create so it doesn't crash if it already exists
        # try:
        #     collection.add(documents=["The company wifi password is 'BlueMonkey42'."], ids=["doc1"])
        # except:
        #     pass


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
    # In a real enterprise app, would use JWT tokens.
    admin_password: str
    user_id: str  # NEW: The API must accept an ID with the upload
    content: str


# ==========================================
# 3. CORE AI FUNCTIONS (Unchanged from Phase 10)
# ==========================================

def get_embedding(text):
    print(f"[SERVER LOG] STARTING EMBEDDING FOR: {text[:20]}...")
    hf_key = os.getenv("HUGGINGFACE_API_KEY", "").strip()

    try:
        client = InferenceClient(token=hf_key)
        # We call the model
        vector = client.feature_extraction(text, model="BAAI/bge-small-en-v1.5")

        # DEBUG LOG: This will show us EXACTLY what HF is sending back
        print(f"[DEBUG] Raw Vector Type: {type(vector)}")

        # Convert to list if it's a numpy array or tensor
        if hasattr(vector, "tolist"):
            vector = vector.tolist()

        # Ensure it's a flat list of floats
        if isinstance(vector, list):
            if len(vector) > 0 and isinstance(vector[0], list):
                vector = vector[0]  # Flatten if nested

            print(f"[SERVER LOG] Success! Vector length: {len(vector)}")
            return vector

        print("[ERROR] Vector is not a list or recognizable format.")
        return None

    except Exception as e:
        print(f"[ERROR] CRITICAL SDK FAILURE: {e}")
        return None


def get_manager_decision(user_text, history_list=[]):
    # 1. Give the Manager context so it doesn't get confused by short prompts like "Why?" or "Show me"
    recent_context = ""
    if len(history_list) > 1:
        # Grab the last 4 messages to establish the topic
        for msg in history_list[-5:-1]:
            recent_context += f"{msg['role'].upper()}: {msg['content'][:100]}...\n"

    orchestrator_prompt = [
        {"role": "system", "content": """You are the Master Routing Orchestrator. 
Analyze the user's input and route it to the correct departments. Output ONLY a comma-separated list of department names. NO explanations.

ROUTING RULES:
1. 'RAG' : USE THIS FIRST for ANY questions about company data, rules, internal facts, or if the user says "check database".
2. 'WEB' : Use for live events, weather, world news, or general web knowledge.
3. 'MATH' : Use ONLY if there is a mathematical equation to solve.
4. 'CHAT' : Use for pure conversation, follow-up questions to previous topics, or small talk."""},
        {"role": "user", "content": f"RECENT CHAT HISTORY:\n{recent_context}\n\nUSER'S LATEST PROMPT: {user_text}"}
    ]

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "llama-3.1-8b-instant", "messages": orchestrator_prompt, "temperature": 0.0}

    try:
        response = requests.post(CLOUD_URL, headers=headers, json=payload, timeout=10)
        return response.json()["choices"][0]["message"]["content"].strip().upper()
    except Exception as e:
        print(f"[ERROR] Manager failed: {e}")
        return "CHAT"

# The Micro Agent
def get_search_query(user_text):
    today = datetime.now().strftime("%B %d, %Y")
    current_year = datetime.now().year

    topic_prompt = [
        {"role": "system", "content": f"""You are a strict SEO Extraction Tool. Today is {today}.
        Your job is to output a search query ONLY if the user asks about current events, news, or weather.

        CRITICAL RULES:
        1. If the user is making small talk (e.g., "Hi", "How are you"), output 'NONE'.
        2. If the user is asking a math question (e.g., "5+5"), output 'NONE'.
        3. If the user is asking about internal company data (e.g., "wifi", "ceo"), output 'NONE'.
        4. Output EXACTLY the search string or the word 'NONE'. 
        5. DO NOT provide explanations, DO NOT say "No relevant topic".

        EXAMPLES:
        User: "Hi there" -> NONE
        User: "What is 10*10?" -> NONE
        User: "Who is the PM of India?" -> PM of India {current_year}
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


@app.get("/history/{user_id}")
async def get_user_history(user_id: str, limit: int = 15, offset: int = 0):
    print(f"\n--- FETCHING HISTORY FOR [{user_id}] | OFFSET: {offset} ---")
    try:
        # .range() is how Supabase handles Pagination (Offset and Limit)
        response = supabase.table("messages") \
            .select("role, content") \
            .eq("user_id", user_id) \
            .order("created_at", desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()

        messages = response.data

        # THE ARCHITECTURAL FIX: We NO LONGER reverse the list!
        # The new React Native FlatList needs the newest messages at index 0.
        return {"status": "success", "data": messages}

    except Exception as e:
        print(f"[DB ERROR] Failed to fetch history: {e}")
        return {"status": "error", "message": "Could not fetch history"}

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

    # 2. Background Janitor (UPGRADED CONTINUITY ENGINE)
    # We allow a more natural conversation runway before compressing memory
    if len(user_history) > 20:
        print(f"[SERVER LOG] Compressing memory for {request.user_id}...")

        # Compress the older history data, but preserve the last 4 messages intact
        compressed_text = compress_memory(user_history[:-5])

        new_memory = [user_history[0]]  # Keep the Base System Prompt
        new_memory.append({"role": "system", "content": f"Past Conversation Summary:\n{compressed_text}"})
        new_memory.extend(user_history[-5:])  # Append the recent active dialogue rows

        active_sessions[request.user_id] = new_memory
        user_history = active_sessions[request.user_id]

    # 3. Manager Routing (UPGRADED)
    # We now hand the Manager the conversation history so it can read the room!
    decision = get_manager_decision(request.prompt, user_history)
    print(f"[SERVER LOG] Manager routed to: {decision}")

    # 4. The Pipeline
    temp_memory = user_history.copy()
    collected_context = ""

    if "RAG" in decision:
        print("[SERVER LOG] RAG Department activated. Translating prompt to vector...")
        # 1. Translate the user's english question into Math (Vector)
        user_vector = get_embedding(request.prompt)

        if user_vector:
            print("[SERVER LOG] Searching Supabase Vault...")
            # 2. Ask Supabase to find the closest matching document
            results = supabase.rpc(
                'match_company_docs',
                {'query_embedding': user_vector, 'match_threshold': 0.3,
                        'match_count': 1, 'p_user_id': request.user_id}        # THE KEY: Hand the security badge to the database
            ).execute()

            # 3. If a match is found, add it to the AI's context
            if results.data and len(results.data) > 0:
                doc_content = results.data[0]['content']
                collected_context += f"<internal_company_data>\n{doc_content}\n</internal_company_data>\n\n"
                print(f"[SERVER LOG] Found relevant doc: {doc_content[:30]}...")


    if "WEB" in decision:
        optimized_query = get_search_query(request.prompt).strip().upper()

        # ELITE FILTER: Check if it's actually a query or just the AI talking
        # If it's too long, contains 'NONE', or says "NO RELEVANT", we kill it.
        forbidden_phrases = ["NONE", "NO RELEVANT", "NOT SPECIFIED", "SORRY"]
        is_invalid = any(phrase in optimized_query for phrase in forbidden_phrases)

        if not is_invalid and len(optimized_query) > 1:
            print(f"[SERVER LOG] Valid Search Query Found: {optimized_query}")
            live_data = perform_web_search(optimized_query)
            collected_context += f"<live_web_data query='{optimized_query}'>\n{live_data}\n</live_web_data>\n\n"
        else:
            print(f"[SERVER LOG] Web search skipped. Agent returned: {optimized_query}")

    if "MATH" in decision:
        # 1. THE TRANSLATOR: Convert English math words to symbols first
        clean_prompt = request.prompt.lower()
        clean_prompt = clean_prompt.replace("times", "*").replace("multiplied by", "*").replace("x", "*")
        clean_prompt = clean_prompt.replace("plus", "+").replace("add", "+")
        clean_prompt = clean_prompt.replace("minus", "-").replace("subtract", "-")
        clean_prompt = clean_prompt.replace("divided by", "/").replace("divide", "/")

        # 2. THE LOGIC GATE: Now we check the translated prompt
        if any(op in clean_prompt for op in ['+', '-', '*', '/']):
            # 3. THE SURGEON: Vacuum up everything except numbers and math symbols
            math_expression = re.sub(r'[^0-9\+\-\*\/\(\)\.]', '', clean_prompt)
            print(f"[SERVER LOG] MATH Department extracted equation: '{math_expression}'")
            try:
                answer = calculate_math(math_expression)
                print(f"[SERVER LOG] MATH Department calculated: {answer}")
                collected_context += f"<math_calculation>\nThe exact mathematical answer to the user's equation is: {answer}\n</math_calculation>\n\n"
            except Exception as e:
                print(f"[SERVER LOG] MATH failed: {e}")

    # 5. Final Synthesis (UPGRADED)
    if collected_context != "":
        # THE FIX: We stop overwriting the user's prompt!
        # We inject the data as a system whisper right before their question.
        context_whisper = {
            "role": "system",
            "content": f"INTERNAL SYSTEM DATA VAULT:\n{collected_context}\n\nRule: Use this data to help answer the user if relevant. If they are just chatting normally, ignore this data and rely on the conversation history."
        }
        # Python's .insert(-1) places this whisper right before the user's last message!
        temp_memory.insert(-1, context_whisper)

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


@app.post("/upload-doc")
async def upload_company_document(doc: DocumentUpload):
    print("\n--- NEW DOCUMENT UPLOAD REQUEST ---")

    # 1. Basic Security Gate
    # DO NOT hardcode passwords in production. We use environment variables.
    # Add ADMIN_SECRET_PASSWORD to your .env and Render variables.
    secure_password = os.getenv("ADMIN_SECRET_PASSWORD", "supersecret123")
    if doc.admin_password != secure_password:
        print("[SECURITY ALERT] Unauthorized upload attempt.")
        return {"status": "error", "message": "Unauthorized. Incorrect admin password."}

    # 2. Translate English to Math (Vector)
    print(f"[SERVER LOG] Translating document to vector: {doc.content[:30]}...")
    vector_math = get_embedding(doc.content)

    if not vector_math:
        return {"status": "error", "message": "Failed to translate document into a vector."}

    # 3. Save to Supabase pgvector Vault
    try:
        supabase.table("company_docs").insert({
            "user_id": doc.user_id,  # THE STAMP: Locks this document to this user
            "content": doc.content,
            "embedding": vector_math
        }).execute()

        print("[DB LOG] Document successfully secured in vault.")
        return {"status": "success", "message": "Document uploaded and embedded successfully."}

    except Exception as e:
        print(f"[DB ERROR] Failed to save document: {e}")
        return {"status": "error", "message": f"Database error: {str(e)}"}

if __name__ == "__main__":
    # Dynamically grab the port Render assigns, or default to 8000 for your local machine
    port = int(os.environ.get("PORT", 8009))
    # Remove 'reload=True' in production. It wastes memory and is only for local dev.
    uvicorn.run("main:app", host="0.0.0.0", port=port)