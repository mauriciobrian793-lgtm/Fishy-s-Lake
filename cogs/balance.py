import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument
from utils import check_cooldown


class Balance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    # -------------------------
    # GET OR CREATE USER (FIXED)
    # -------------------------
    def get_user(self, guild_id, user_id, name):
        return self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "balance": 0,
                    "name": name
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    # -------------------------
    # COMMAND
    # -------------------------
    @app_commands.command(
        name="balance",
        description="View your balance or another user's balance"
    )
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):

        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ This command can only be used in servers.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        # -------------------------
        # COOLDOWN
        # -------------------------
        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "balance",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        # -------------------------
        # DEFAULT USER
        # -------------------------
        if user is None:
            user = interaction.user

        data = self.get_user(
            interaction.guild.id,
            user.id,
            user.name
        )

        balance = data.get("balance", 0)

        # -------------------------
        # EMBED
        # -------------------------
        embed = discord.Embed(
            title="🏦 Balance",
            color=discord.Color.green()
        )

        embed.add_field(
            name="👤 User",
            value=user.mention,
            inline=True
        )

        embed.add_field(
            name="💰 Money",
            value=f"${balance}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Balance(bot))