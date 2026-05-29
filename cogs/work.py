import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown
from pymongo import ReturnDocument  # ✅ FIXED IMPORT


class Work(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # Motor collection

    # -------------------------
    # GET OR CREATE USER (ASYNC)
    # -------------------------
    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
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
            return_document=ReturnDocument.AFTER
        )

    # -------------------------
    # UPDATE BALANCE
    # -------------------------
    async def update_balance(self, guild_id, user_id, amount):
        await self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}},
            upsert=True
        )

    # -------------------------
    # COMMAND
    # -------------------------
    @app_commands.command(
        name="work",
        description="Work to earn money"
    )
    async def work(self, interaction: discord.Interaction):

        await interaction.response.defer()  # ✅ prevents "did not respond"

        if not interaction.guild:
            return await interaction.followup.send(
                "Guild only command.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "work",
            settings
        )

        if not allowed:
            return await interaction.followup.send(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

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

        await self.update_balance(
            interaction.guild.id,
            interaction.user.id,
            earnings
        )

        updated = await self.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.name
        )

        embed = discord.Embed(
            title="💼 Work Result",
            description=result_text,
            color=discord.Color.green()
        )

        embed.add_field(name="💰 Earned", value=f"${earnings}", inline=True)
        embed.add_field(
            name="🏦 Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Work(bot))