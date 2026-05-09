import discord
import requests
import os
from dotenv import load_dotenv

# === 1. CONFIGURATION ===
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

