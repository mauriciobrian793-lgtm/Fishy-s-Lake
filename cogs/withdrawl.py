import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


class Withdraw(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy

    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0,
                    "bank": 0
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    async def update_bank(self, guild_id, user_id, wallet_change=0, bank_change=0):
        await self.economy.update_one(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$inc": {
                    "balance": wallet_change,
                    "bank": bank_change
                }
            },
            upsert=True
        )

    @app_commands.command(name="withdraw", description="Withdraw money from your bank")
    async def withdraw(self, interaction: discord.Interaction, amount: str):

        if not interaction.guild:
            return await interaction.response.send_message("Guild only command.")

        user = await self.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.name
        )

        bank = user.get("bank", 0)

        # -------------------------
        # HANDLE "all"
        # -------------------------
        if amount.lower() == "all":
            withdraw_amount = bank
        else:
            try:
                withdraw_amount = int(amount)
            except ValueError:
                return await interaction.response.send_message("❌ Please enter a valid number or `all`.")

        # -------------------------
        # VALIDATION FIXES
        # -------------------------
        if withdraw_amount <= 0:
            return await interaction.response.send_message("❌ You must withdraw more than $0.")

        if withdraw_amount > bank:
            return await interaction.response.send_message(
                f"❌ You only have **${bank}** in your bank."
            )

        # -------------------------
        # UPDATE MONGO SAFELY
        # -------------------------
        await self.update_bank(
            interaction.guild.id,
            interaction.user.id,
            wallet_change=withdraw_amount,
            bank_change=-withdraw_amount
        )

        await interaction.response.send_message(
            f"💰 Withdrew **${withdraw_amount}** from your bank!"
        )


async def setup(bot):
    await bot.add_cog(Withdraw(bot))