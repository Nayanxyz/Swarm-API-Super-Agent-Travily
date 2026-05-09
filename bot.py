import discord
import requests
import os
from dotenv import load_dotenv

# === 1. CONFIGURATION ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# [IMPORTANT]: Paste your actual Render URL here!
API_URL = "https://swarm-api-super-agent-travily.onrender.com/chat"

# Give the bot permission to read messages
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


