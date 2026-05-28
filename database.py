from pymongo import MongoClient

MONGO_URL = "mongodb+srv://mauriciobrian793_db_user:<db_password>@fishyeconomybotcluster.ijsludq.mongodb.net/"

client = MongoClient(MONGO_URL)

db = client["fishy_bot"]
economy = db["economy"]

def get_user(guild_id, user_id):
    data = economy.find_one({
        "guild_id": str(guild_id),
        "user_id": str(user_id)
    })

    if not data:
        data = {
            "guild_id": str(guild_id),
            "user_id": str(user_id),
            "balance": 0
        }
        economy.insert_one(data)

    return data


def add_money(guild_id, user_id, amount):
    economy.update_one(
        {"guild_id": str(guild_id), "user_id": str(user_id)},
        {"$inc": {"balance": amount}}
    )


def remove_money(guild_id, user_id, amount):
    economy.update_one(
        {"guild_id": str(guild_id), "user_id": str(user_id)},
        {"$inc": {"balance": -amount}}
    )