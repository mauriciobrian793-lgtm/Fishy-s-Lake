from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://mauriciobrian793_db_user:Uspkajyvgc@fishyeconomybotcluster.ijsludq.mongodb.net/?appName=Fishyeconomybotcluster"

client = AsyncIOMotorClient(MONGO_URL)

db = client["fishy_bot"]
economy = db["economy"]

# -------------------------
# GET USER
# -------------------------
async def get_user(guild_id, user_id):
    data = await economy.find_one({
        "guild_id": str(guild_id),
        "user_id": str(user_id)
    })

    if not data:
        data = {
            "guild_id": str(guild_id),
            "user_id": str(user_id),
            "balance": 0
        }
        await economy.insert_one(data)

    return data

# -------------------------
# ADD MONEY
# -------------------------
async def add_money(guild_id, user_id, amount):
    await economy.update_one(
        {"guild_id": str(guild_id), "user_id": str(user_id)},
        {"$inc": {"balance": amount}},
        upsert=True
    )

# -------------------------
# REMOVE MONEY
# -------------------------
async def remove_money(guild_id, user_id, amount):
    await economy.update_one(
        {"guild_id": str(guild_id), "user_id": str(user_id)},
        {"$inc": {"balance": -amount}},
        upsert=True
    )