import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown


class Work(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # MongoDB collection

    # =========================
    # GET OR CREATE USER
    # =========================
    def get_user(self, guild_id, user_id, name):
        return self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0
                }
            },
            upsert=True,
            return_document=True
        )

    # =========================
    # UPDATE BALANCE
    # =========================
    def update_balance(self, guild_id, user_id, amount):
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}}
        )

    # =========================
    # COMMAND
    # =========================
    @app_commands.command(
        name="work",
        description="Work to earn money"
    )
    async def work(self, interaction: discord.Interaction):

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "work",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        guild_id = interaction.guild.id
        user_id = interaction.user.id

        user = self.get_user(guild_id, user_id, interaction.user.name)

        earnings = random.randint(100, 2000)

        jobs = [
            "You worked at a pizza shop 🍕",
            "You delivered packages 📦",
            "You coded websites 💻",
            "You fixed cars 🔧",
            "You worked at a store 🛒",
            "You did freelance art 🎨",
        ]

        result_text = random.choice(jobs)

        # add money
        self.update_balance(guild_id, user_id, earnings)

        updated = self.get_user(guild_id, user_id, interaction.user.name)

        embed = discord.Embed(
            title="💼 Work Result",
            description=result_text,
            color=discord.Color.green()
        )

        embed.add_field(
            name="💰 Earned",
            value=f"${earnings}",
            inline=True
        )

        embed.add_field(
            name="🏦 Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Work(bot))