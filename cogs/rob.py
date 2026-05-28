import discord
from discord.ext import commands
from discord import app_commands
import random
from utils import check_cooldown


class Rob(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # MongoDB collection

    # =========================
    # USER SYSTEM
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

    def update_balance(self, guild_id, user_id, amount):
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}}
        )

    # =========================
    # COMMAND
    # =========================
    @app_commands.command(name="rob", description="Rob another user")
    async def rob(self, interaction: discord.Interaction, user: discord.Member):

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        # =========================
        # COOLDOWN CHECK
        # =========================
        allowed, remaining = check_cooldown(
            interaction.guild.id,
            interaction.user.id,
            "rob",
            settings
        )

        if not allowed:
            return await interaction.response.send_message(
                f"⏳ Wait {remaining}s before using this command again.",
                ephemeral=True
            )

        # =========================
        # SELF ROB CHECK
        # =========================
        if interaction.user.id == user.id:
            return await interaction.response.send_message(
                "❌ You cannot rob yourself.",
                ephemeral=True
            )

        guild_id = interaction.guild.id

        robber = self.get_user(guild_id, interaction.user.id, interaction.user.name)
        victim = self.get_user(guild_id, user.id, user.name)

        robber_balance = robber.get("balance", 0)
        victim_balance = victim.get("balance", 0)

        # =========================
        # NO MONEY CHECK
        # =========================
        if victim_balance <= 0:
            return await interaction.response.send_message(
                f"❌ {user.mention} has no money to rob.",
                ephemeral=True
            )

        success = random.randint(1, 100) <= 50

        # =========================
        # SUCCESS
        # =========================
        if success:

            amount = random.randint(1, victim_balance)

            self.update_balance(guild_id, user.id, -amount)
            self.update_balance(guild_id, interaction.user.id, amount)

            result_text = f"💰 You stole **${amount}** from {user.mention}!"
            color = discord.Color.green()

        # =========================
        # FAIL
        # =========================
        else:

            loss = min(random.randint(1, 1000), robber_balance)

            self.update_balance(guild_id, interaction.user.id, -loss)

            result_text = f"🚓 You got caught and lost **${loss}**!"
            color = discord.Color.red()

        # =========================
        # REFRESH DATA
        # =========================
        updated = self.economy.find_one(
            {"guild_id": str(guild_id), "user_id": str(interaction.user.id)}
        ) or {"balance": 0}

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

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Rob(bot))