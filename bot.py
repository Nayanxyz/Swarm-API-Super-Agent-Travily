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

        # SAFETY NET 1: The Empty Ping
        if not prompt:
            await message.reply("You called? Ask me a question!")
            return

        # Show the "Bot is typing..." animation in Discord
        async with message.channel.typing():

            # I highly recommend adding a prefix like "discord_" so when you look at
            # your Supabase logs, you know exactly which frontend this user came from!
            payload = {
                "user_id": f"discord_{message.author.id}",
                "prompt": prompt
            }

            try:
                # SAFETY NET 2: The Timeout (Prevents the bot from freezing if Render is asleep)
                response = requests.post(API_URL, json=payload, timeout=45)

                if response.status_code == 200:
                    data = response.json()
                    answer = data["final_answer"]

                    # SAFETY NET 3: The 2000 Character Limit
                    # If it's too long, we cut it off at 1996 chars and add "..."
                    if len(answer) > 2000:
                        answer = answer[:1996] + "..."

                    # Reply in Discord with the AI's final answer
                    await message.reply(answer)
                else:
                    await message.reply(f"The Swarm backend threw an error: {response.status_code}")

            # Catch timeouts specifically to give the user a helpful message
            except requests.exceptions.Timeout:
                await message.reply("My brain (Render Server) is taking too long to respond. Try again in a minute!")
            except Exception as e:
                print(f"Error: {e}")
                await message.reply("Failed to connect to the cloud brain. 🔌")


# Turn on the power
client.run(TOKEN)