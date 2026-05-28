import discord
from discord.ext import commands
from discord import app_commands
from utils import check_cooldown


class Give(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy  # MongoDB collection

    # =========================
    # USER SYSTEM
    # =========================
    def get_user(self, guild_id, user_id, username):
        data = self.economy.find_one({
            "guild_id": str(guild_id),
            "user_id": str(user_id)
        })

        if not data:
            data = {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "name": username,
                "balance": 0
            }
            self.economy.insert_one(data)

        return data

    def update_balance(self, guild_id, user_id, amount):
        self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {"$inc": {"balance": amount}}
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

        settings = self.bot.settings.setdefault(str(interaction.guild.id), {})

        # =========================
        # COOLDOWN CHECK
        # =========================
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

        # =========================
        # VALIDATION
        # =========================
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

        giver = self.get_user(guild_id, interaction.user.id, interaction.user.name)
        receiver = self.get_user(guild_id, user.id, user.name)

        giver_balance = giver.get("balance", 0)

        if giver_balance < amount:
            return await interaction.response.send_message(
                "❌ You don't have enough money.",
                ephemeral=True
            )

        # =========================
        # TRANSFER
        # =========================
        self.update_balance(guild_id, interaction.user.id, -amount)
        self.update_balance(guild_id, user.id, amount)

        new_balance = giver_balance - amount

        # =========================
        # EMBED
        # =========================
        embed = discord.Embed(
            title="💸 Money Transferred",
            color=discord.Color.green()
        )

        embed.add_field(name="👤 From", value=interaction.user.mention, inline=True)
        embed.add_field(name="👤 To", value=user.mention, inline=True)
        embed.add_field(name="💰 Amount", value=f"${amount}", inline=False)
        embed.add_field(name="🏦 Your New Balance", value=f"${new_balance}", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Give(bot))