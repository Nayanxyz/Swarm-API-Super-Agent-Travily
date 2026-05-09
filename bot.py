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


# === 2. EVENT: BOT WAKES UP ===
@client.event
async def on_ready():
    print(f"✅ {client.user} has connected to Discord and is listening!")


# === 3. EVENT: A MESSAGE IS SENT ===
@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Only respond if the user @mentions the bot
    if client.user in message.mentions:

        # Strip the @mention tag out of the text so the API only gets the question
        prompt = message.content.replace(f'<@{client.user.id}>', '').strip()

