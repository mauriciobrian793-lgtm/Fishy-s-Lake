import discord
from discord.ext import commands
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os

# -------------------------
# LOAD ENV
# -------------------------
load_dotenv()

TOKEN = os.getenv("TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

if not TOKEN:
    raise RuntimeError("TOKEN not found in .env")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL not found in .env")

# -------------------------
# BOT SETUP
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents)

bot.settings = {}

# -------------------------
# MONGO (ASYNC)
# -------------------------
client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000
)

db = client["economy_db"]
bot.economy = db["economy"]

# -------------------------
# READY EVENT
# -------------------------
@bot.event
async def on_ready():
    print("=================================")
    print(f"Logged in as {bot.user}")
    print(f"Guilds: {len(bot.guilds)}")
    print("Bot is ONLINE and ready!")
    print("=================================")

# -------------------------
# LOAD COGS
# -------------------------
@bot.event
async def setup_hook():
    print("Loading cogs...")

    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")
            except Exception as e:
                print(f"FAILED cog: {filename}")
                print(e)

    print("Syncing slash commands...")

    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print("Sync error:", e)

# -------------------------
# RUN BOT
# -------------------------
bot.run(TOKEN)