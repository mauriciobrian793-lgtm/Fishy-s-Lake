import time

COOLDOWNS = {}

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

    COOLDOWNS[key] = now

    # safer cleanup (prevents lag spikes)
    if len(COOLDOWNS) > 5000:
        for k in list(COOLDOWNS)[:1000]:
            COOLDOWNS.pop(k, None)

    return True, 0