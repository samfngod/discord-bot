import os
import aiohttp
import random
import string
import discord
from discord.ext import commands
import asyncio
from aiohttp import web

# ----------------- CONFIG -----------------
API_URL = os.getenv("API_URL", "").rstrip("/")       # es: https://auth-api-xxxxx.onrender.com
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
PORT = int(os.environ.get("PORT", 12345))           # Cambiata porta, Render assegna variabile PORT

# ----------------- BOT DISCORD -----------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def make_code(n: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "X" + "".join(random.choice(alphabet) for _ in range(n))

@bot.event
async def on_ready():
    print(f"[BOT] Online come {bot.user} • Slash commands sincronizzati")
    try:
        await bot.tree.sync()
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
        await interaction.response.send_message(
            f"Il tuo codice: **{code}** (valido 15 min).", ephemeral=True
        )
    else:
        await interaction.response.send_message("Errore nella creazione del codice.", ephemeral=True)
        print("[BOT] Risposta API:", data)

# ----------------- SERVER WEB PER RENDER -----------------
async def handle(request):
    return web.Response(text="Bot online ✔️")

web_app = web.Application()
web_app.add_routes([web.get("/", handle)])

async def start_web_server():
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"[WEB] Server web in ascolto su porta {PORT}")

# ----------------- MAIN -----------------
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Manca DISCORD_TOKEN nelle variabili d'ambiente.")
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())  # avvia server web in parallelo
    bot.run(DISCORD_TOKEN)
