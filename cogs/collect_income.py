import discord
from discord.ext import commands
from discord import app_commands
from utils import check_cooldown
from pymongo import ReturnDocument


class CollectIncome(commands.Cog):

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
    # ADD MONEY (FIXED)
    # -------------------------
    def add_money(self, guild_id, user_id, amount):
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$inc": {"balance": amount},
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "balance": 0
                }
            },
            upsert=True
        )

    # -------------------------
    # COMMAND
    # -------------------------
    @app_commands.command(
        name="collect_income",
        description="Collect money from your job roles"
    )
    async def collect_income(self, interaction: discord.Interaction):

        await interaction.response.defer()

        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        guild_id = str(interaction.guild.id)
        user = interaction.user

        settings = self.bot.settings.setdefault(guild_id, {})

        # -------------------------
        # COOLDOWN
        # -------------------------
        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "collect_income",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before collecting income again.",
                ephemeral=True
            )

        role_income = settings.get("role_income", {})

        if not role_income:
            return await interaction.response.send_message(
                "❌ No income roles have been set yet.",
                ephemeral=True
            )

        total = 0
        breakdown = []

        for role in user.roles:
            rid = str(role.id)

            if rid in role_income:
                amount = role_income[rid]
                total += amount
                breakdown.append(f"• {role.name}: +${amount}")

        if total == 0:
            return await interaction.response.send_message(
                "❌ You don't have any income roles.",
                ephemeral=True
            )

        # -------------------------
        # GIVE MONEY
        # -------------------------
        self.add_money(guild_id, user.id, total)
        updated = self.get_user(guild_id, user.id, user.name)

        # -------------------------
        # EMBED
        # -------------------------
        embed = discord.Embed(
            title="💰 Income Collected",
            color=discord.Color.green()
        )

        embed.add_field(
            name="💼 Breakdown",
            value="\n".join(breakdown),
            inline=False
        )

        embed.add_field(
            name="💵 Total Earned",
            value=f"${total}",
            inline=True
        )

        embed.add_field(
            name="🏦 New Balance",
            value=f"${updated.get('balance', 0)}",
            inline=True
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(CollectIncome(bot))