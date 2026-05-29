import time

COOLDOWNS = {}

# -------------------------
# COOLDOWN CHECK
# -------------------------
def check_cooldown(guild_id, user_id, command, settings):
    guild_id = str(guild_id)

    cooldown = settings.get("cooldowns", {}).get(command, 0)
    key = f"{guild_id}:{user_id}:{command}"
    now = time.time()

    last_used = COOLDOWNS.get(key)

    if last_used:
        elapsed = now - last_used
        remaining = cooldown - elapsed

        if remaining > 0:
            return False, int(remaining)

    # set cooldown AFTER passing check
    COOLDOWNS[key] = now

    # cleanup to prevent memory spam
    if len(COOLDOWNS) > 5000:
        for k in list(COOLDOWNS)[:1000]:
            COOLDOWNS.pop(k, None)

    return True, 0


# -------------------------
# (OPTIONAL) HELPERS FOR MONGO
# -------------------------
async def get_settings(bot, guild_id):
    settings = await bot.settings_db.find_one({"guild_id": str(guild_id)})

    if not settings:
        settings = {
            "guild_id": str(guild_id),
            "cooldowns": {},
            "role_income": {},
            "admin_role_id": None
        }
        await bot.settings_db.insert_one(settings)

    return settings