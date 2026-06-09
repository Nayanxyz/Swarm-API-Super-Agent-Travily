# 🐝 Enterprise AI Swarm (Jango AI)


**Enterprise AI Swarm** is a multi-platform, agentic AI architecture powered by FastAPI, Supabase (pgvector), and LLaMA 3. The system acts as a centralized "brain" (Jango) that intelligently routes user queries to specialized micro-agents for web searching, document retrieval (RAG), math calculations, and general conversation. 

The swarm is accessible from anywhere via three distinct interfaces: a **React Native (Expo)** mobile application, a **Streamlit** web dashboard, and a **Discord** bot.

<p align="center">
  <img width="1906" height="785" alt="Screenshot 2026-06-09 132912" src="https://github.com/user-attachments/assets/aa8580ac-d4b4-432b-a61b-9bc2f688af4f" />
</p>

## ✨ Key Features

* 🧠 **Intelligent Agent Routing:** An orchestrator LLM analyzes incoming prompts and seamlessly routes them to the correct department (`RAG`, `WEB`, `MATH`, or `CHAT`).
* 📚 **Retrieval-Augmented Generation (RAG):** Securely upload company documents and facts to a Supabase pgvector vault. The AI automatically embeds and retrieves this data using HuggingFace (`BAAI/bge-small-en-v1.5`).
* 🌐 **Live Web Search Agent:** Integrates with Tavily API to fetch real-time news, weather, and world events when the user asks about current data.
* 📱 **Multi-Client Architecture:**
    * **iOS/Android App:** Built with React Native & Expo, featuring Supabase Auth and pagination.
    * **Web Vault:** Built with Streamlit for admin knowledge uploading and desktop chatting.
    * **Discord Integration:** A seamless bot for community server interaction.
* 🗄️ **Persistent Neural Memory:** Chat history is persistently stored and paginated from Supabase, ensuring Jango never loses context across sessions.

<p align="center">
  <img src="https://via.placeholder.com/400x400?text=Mobile+App+Screenshot" width="45%">
  &nbsp; &nbsp;
  <img src="https://via.placeholder.com/400x400?text=Streamlit+Web+Screenshot" width="45%">
</p>

## 🛠️ Tech Stack

**Backend & AI Pipeline:**
* **Framework:** FastAPI, Uvicorn
* **Database & Vector Store:** Supabase (PostgreSQL + pgvector)
* **LLM Inference:** Groq API (LLaMA-3.1-8b-instant)
* **Embeddings:** HuggingFace API
* **Live Web Data:** Tavily Search API

**Frontend Clients:**
* **Mobile:** React Native, Expo, Supabase JS Auth
* **Web:** Streamlit
* **Bot:** Discord.py

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* Python 3.10+
* Node.js & npm (for React Native)
* Supabase Project (with pgvector enabled and a `messages` & `company_docs` table)
* API Keys: Groq, HuggingFace, Tavily, Discord Bot Token.

### 2. Environment Variables (`.env`)
Create a `.env` file in the root of your backend directory:

```env
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
HUGGINGFACE_API_KEY=your_hf_key
TAVILY_API_KEY=your_tavily_key
ADMIN_SECRET_PASSWORD=your_secure_admin_password
DISCORD_TOKEN=your_discord_bot_token
```
