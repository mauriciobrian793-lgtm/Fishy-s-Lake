import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import os
from utils import check_cooldown

ECONOMY_FILE = "economy.json"


# -------------------------
# LOAD / SAVE
# -------------------------
def load_economy():
    if not os.path.exists(ECONOMY_FILE):
        return {}

    with open(ECONOMY_FILE, "r") as f:
        return json.load(f)


def save_economy(data):
    with open(ECONOMY_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -------------------------
# COG
# -------------------------
class Crime(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="crime",
        description="Commit a crime for money"
    )
    async def crime(self, interaction: discord.Interaction):

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        # =========================
        # COOLDOWN
        # =========================
        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "crime",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        economy = load_economy()

        # -------------------------
        # USER KEY
        # -------------------------
        user_id = f"{interaction.guild.id}_{interaction.user.id}"

        # ensure user exists
        if user_id not in economy:
            economy[user_id] = {
                "balance": 0,
                "name": interaction.user.name
            }

        success = random.randint(1, 100) <= 40

        # -------------------------
        # SUCCESS
        # -------------------------
        if success:

            earnings = random.randint(0, 10000)

            economy[user_id]["balance"] += earnings
            economy[user_id]["name"] = interaction.user.name

            save_economy(economy)

            success_messages = [
                "You robbed a bank vault 🏦",
                "You hacked an ATM 💻",
                "You stole a luxury car 🚗",
                "You robbed a jewelry store 💎",
            ]

            embed = discord.Embed(
                title="🚔 Crime Successful!",
                description=random.choice(success_messages),
                color=discord.Color.green()
            )

            embed.add_field(
                name="💰 Earned",
                value=f"${earnings}",
                inline=True
            )

        # -------------------------
        # FAIL
        # -------------------------
        else:

            loss = random.randint(1, 1000)

            balance = economy[user_id].get("balance", 0)

            if loss > balance:
                loss = balance

            economy[user_id]["balance"] = balance - loss

            save_economy(economy)

            fail_messages = [
                "You got caught by the police 🚓",
                "Security stopped you 🛑",
                "You failed the robbery 💸",
                "You tripped while escaping 😭",
            ]

            embed = discord.Embed(
                title="❌ Crime Failed!",
                description=random.choice(fail_messages),
                color=discord.Color.red()
            )

            embed.add_field(
                name="💸 Lost",
                value=f"${loss}",
                inline=True
            )

        # -------------------------
        # BALANCE
        # -------------------------
        embed.add_field(
            name="🏦 Balance",
            value=f"${economy[user_id]['balance']}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


# -------------------------
# SETUP
# -------------------------
async def setup(bot):
    await bot.add_cog(Crime(bot))