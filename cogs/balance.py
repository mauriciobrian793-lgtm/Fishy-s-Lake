import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument
from utils import check_cooldown
from utils import get_settings


class Balance(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    # -------------------------
    # GET OR CREATE USER
    # -------------------------
    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0,   # wallet
                    "bank": 0       # 🏦 added bank support
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

        settings = await get_settings(self.bot, interaction.guild.id)

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

        await interaction.response.defer()

        if user is None:
            user = interaction.user

        data = await self.get_user(
            interaction.guild.id,
            user.id,
            user.name
        )

        wallet = data.get("balance", 0)
        bank = data.get("bank", 0)
        total = wallet + bank

        embed = discord.Embed(
            title="🏦 Balance",
            color=discord.Color.green()
        )

        embed.add_field(
            name="👤 User",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="💰 Wallet",
            value=f"${wallet}",
            inline=True
        )

        embed.add_field(
            name="🏦 Bank",
            value=f"${bank}",
            inline=True
        )

        embed.add_field(
            name="🧾 Total",
            value=f"${total}",
            inline=False
        )

        await interaction.followup.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Balance(bot))