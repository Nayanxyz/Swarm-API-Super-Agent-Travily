import discord
import requests
import os
from dotenv import load_dotenv

# === 1. CONFIGURATION ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# [IMPORTANT]: Paste your actual Render URL here!
API_URL = "https://swarm-api-super-agent-travily.onrender.com/chat"

