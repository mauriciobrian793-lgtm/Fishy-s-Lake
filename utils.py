import time

COOLDOWNS = {}

def check_cooldown(guild_id, user_id, command, settings):
    guild_id = str(guild_id)

    cooldown = settings.get("cooldowns", {}).get(command, 0)
    key = f"{guild_id}:{user_id}:{command}"
    now = time.time()

    last_used = COOLDOWNS.get(key)

    if last_used is not None:
        remaining = cooldown - (now - last_used)

        if remaining > 0:
            return False, int(remaining)

    COOLDOWNS[key] = now

    # optional cleanup (prevents memory growth)
    if len(COOLDOWNS) > 5000:
        for k in list(COOLDOWNS.keys())[:1000]:
            del COOLDOWNS[k]

    return True, 0