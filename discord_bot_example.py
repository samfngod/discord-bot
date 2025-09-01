# discord_bot_example.py
# Bot con slash command /gencode che crea un codice one-time
# e lo registra sulla tua API (endpoint /addcode).

import os, aiohttp, random, string
import discord
from discord.ext import commands

API_URL = os.getenv("API_URL", "").rstrip("/")           # es: https://auth-api-xxxxx.onrender.com
# Default di sicurezza: usa ENV; se non presente, fallback alla chiave che mi hai dato (puoi toglierla se vuoi)
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "f9A7d3!X2vQ#8LmRp6ZyT0wB1uH4eKjS")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")           # token del bot dal Developer Portal

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def make_code(n: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "X" + "".join(random.choice(alphabet) for _ in range(n))

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"[BOT] Online come {bot.user} • Slash commands sincronizzati")
    except Exception as e:
        print("[BOT] Errore sync slash:", e)

@bot.tree.command(name="gencode", description="Genera un codice monouso (valido per un breve periodo)")
async def gencode(interaction: discord.Interaction):
    if not API_URL:
        await interaction.response.send_message("API_URL non configurato.", ephemeral=True)
        return

    code = make_code()
    payload = {
        "code": code,
        "ttl_seconds": 900,  # 15 minuti
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
        await interaction.response.send_message(
            f"Il tuo codice: **{code}** (valido 15 min).", ephemeral=True
        )
    else:
        await interaction.response.send_message("Errore nella creazione del codice.", ephemeral=True)
        print("[BOT] Risposta API:", data)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Manca DISCORD_TOKEN nelle variabili d'ambiente.")
    bot.run(DISCORD_TOKEN)
