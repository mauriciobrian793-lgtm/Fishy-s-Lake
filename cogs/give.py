import discord
from discord.ext import commands
from discord import app_commands
from utils import check_cooldown
from pymongo import ReturnDocument  # ✅ FIXED IMPORT


class Give(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # Motor collection

    # =========================
    # USER SYSTEM (ASYNC FIXED)
    # =========================
    async def get_user(self, guild_id, user_id, username):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": username,
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
    @app_commands.command(
        name="give",
        description="Give money to another user"
    )
    async def give(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        amount: int
    ):

        if not interaction.guild:
            return await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        if user.bot:
            return await interaction.response.send_message(
                "❌ You cannot give money to bots.",
                ephemeral=True
            )

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "give",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        if user.id == interaction.user.id:
            return await interaction.response.send_message(
                "❌ You can't give money to yourself.",
                ephemeral=True
            )

        if amount <= 0:
            return await interaction.response.send_message(
                "❌ Amount must be greater than 0.",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        giver = await self.get_user(guild_id, interaction.user.id, interaction.user.name)

        giver_balance = giver.get("balance", 0)

        if giver_balance < amount:
            return await interaction.response.send_message(
                "❌ You don't have enough money.",
                ephemeral=True
            )

        # =========================
        # TRANSFER
        # =========================
        await self.update_balance(guild_id, interaction.user.id, -amount)
        await self.update_balance(guild_id, user.id, amount)

        updated_giver = await self.get_user(
            guild_id,
            interaction.user.id,
            interaction.user.name
        )

        embed = discord.Embed(
            title="💸 Money Transferred",
            color=discord.Color.green()
        )

        embed.add_field(name="👤 From", value=interaction.user.mention, inline=True)
        embed.add_field(name="👤 To", value=user.mention, inline=True)
        embed.add_field(name="💰 Amount", value=f"${amount}", inline=False)
        embed.add_field(
            name="🏦 Your New Balance",
            value=f"${updated_giver.get('balance', 0)}",
            inline=False
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Give(bot))