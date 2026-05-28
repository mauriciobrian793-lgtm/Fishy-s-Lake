import discord
from discord.ext import commands
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents)

bot.settings = {}

# -------------------------
# MONGO (MUST BE FIRST)
# -------------------------
client = MongoClient("mongodb+srv://mauriciobrian793_db_user:<db_password>@fishyeconomybotcluster.ijsludq.mongodb.net/")
db = client["economy_db"]
bot.economy = db["economy"]

# -------------------------
# READY EVENT (IMPORTANT DEBUG)
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
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

# -------------------------
# RUN
# -------------------------
bot.run(TOKEN)