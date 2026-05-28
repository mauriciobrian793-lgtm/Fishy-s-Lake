import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown
from pymongo import ReturnDocument  # IMPORTANT (you were missing this)


class Rob(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # Motor collection

    # =========================
    # USER SYSTEM (ASYNC FIXED)
    # =========================
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

    async def update_balance(self, guild_id, user_id, amount):
        await self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}},
            upsert=True
        )

    # =========================
    # COMMAND
    # =========================
    @app_commands.command(name="rob", description="Rob another user")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):

        await interaction.response.defer()

        if not interaction.guild:
            return await interaction.followup.send(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        if user.bot:
            return await interaction.followup.send(
                "❌ You cannot rob bots.",
                ephemeral=True
            )

        if interaction.user.id == user.id:
            return await interaction.followup.send(
                "❌ You cannot rob yourself.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "rob",
            settings
        )

        if not allowed:
            return await interaction.followup.send(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        robber = await self.get_user(guild_id, interaction.user.id, interaction.user.name)
        victim = await self.get_user(guild_id, user.id, user.name)

        victim_balance = victim.get("balance", 0)

        if victim_balance <= 0:
            return await interaction.followup.send(
                f"❌ {user.mention} has no money to rob.",
                ephemeral=True
            )

        success = random.randint(1, 100) <= 50

        # =========================
        # SUCCESS
        # =========================
        if success:
            amount = random.randint(1, max(1, victim_balance))

            await self.update_balance(guild_id, user.id, -amount)
            await self.update_balance(guild_id, interaction.user.id, amount)

            result_text = f"💰 You stole **${amount}** from {user.mention}!"
            color = discord.Color.green()

        # =========================
        # FAIL
        # =========================
        else:
            robber_balance = robber.get("balance", 0)

            loss = random.randint(1, min(1000, max(1, robber_balance)))

            await self.update_balance(guild_id, interaction.user.id, -loss)

            result_text = f"🚓 You got caught and lost **${loss}**!"
            color = discord.Color.red()

        updated = await self.get_user(guild_id, interaction.user.id, interaction.user.name)

        embed = discord.Embed(
            title="💥 Robbery Result",
            description=result_text,
            color=color
        )

        embed.add_field(
            name="🏦 Your Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        embed.add_field(
            name="👤 Target",
            value=user.mention,
            inline=True
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Rob(bot))