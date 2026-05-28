import time

COOLDOWNS = {}

def check_cooldown(guild_id, user_id, command, settings):
    guild_id = str(guild_id)

    cooldown = settings.get("cooldowns", {}).get(command, 0)

    key = f"{guild_id}:{user_id}:{command}"
    now = time.time()

    if key in COOLDOWNS:
        remaining = cooldown - (now - COOLDOWNS[key])
        if remaining > 0:
            return False, int(remaining)

    COOLDOWNS[key] = now
    return True, 0