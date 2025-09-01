import os
import aiohttp
import random
import string
import discord
from discord.ext import commands, tasks
import asyncio

# ----------------- CONFIG -----------------
API_URL = os.getenv("API_URL", "").rstrip("/")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")

# ----------------- BOT DISCORD -----------------
intents = discord.Intents.default()
intents.message_content = True  # abilita contenuto dei messaggi
bot = commands.Bot(command_prefix="!", intents=intents)

def make_code(n: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "X" + "".join(random.choice(alphabet) for _ in range(n))

@bot.event
async def on_ready():
    print(f"[BOT] Online come {bot.user}")
    try:
        await bot.tree.sync()
        print("[BOT] Slash commands sincronizzati")
    except Exception as e:
        print("[BOT] Errore sync slash:", e)
    comando_automatico.start()  # avvia task periodico

# Comando generico di esempio
@bot.tree.command(name="gencode", description="Genera un codice monouso")
async def gencode(interaction: discord.Interaction):
    if not API_URL:
        await interaction.response.send_message("API_URL non configurato.", ephemeral=True)
        return

    code = make_code()
    payload = {
        "code": code,
        "ttl_seconds": 900,
        "metadata": {"discord_id": str(interaction.user.id)}
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_URL}/addcode",
                headers={"X-API-KEY": ADMIN_API_KEY, "Content-Type": "application/json"},
                json=payload,
                timeout=10
            ) as resp:
                data = await resp.json()
    except Exception as e:
        await interaction.response.send_message("Errore di connessione all'API.", ephemeral=True)
        print("[BOT] Errore HTTP:", e)
        return

    if data.get("status") == "added":
        await interaction.response.send_message(f"Il tuo codice: **{code}** (valido 15 min).", ephemeral=True)
    else:
        await interaction.response.send_message("Errore nella creazione del codice.", ephemeral=True)
        print("[BOT] Risposta API:", data)

# ----------------- TASK AUTOMATICO OGNI 5 MIN -----------------
@tasks.loop(minutes=5)
async def comando_automatico():
    channel_id = 123456789012345678  # metti l'ID del canale corretto
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("!tuocomando")  # comando da eseguire ogni 5 minuti

# ----------------- MAIN -----------------
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Manca DISCORD_TOKEN nelle variabili d'ambiente.")
    bot.run(DISCORD_TOKEN)
