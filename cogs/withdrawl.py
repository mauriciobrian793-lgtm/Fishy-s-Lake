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

        if amount.lower() == "all":
            amount = bank
        else:
            try:
                amount = int(amount)
            except:
                return await interaction.response.send_message("❌ Invalid amount.")

        if amount <= 0:
            return await interaction.response.send_message("❌ Amount must be greater than 0.")

        if bank < amount:
            return await interaction.response.send_message("❌ Not enough money in bank.")

        await self.update_bank(
            interaction.guild.id,
            interaction.user.id,
            wallet_change=amount,
            bank_change=-amount
        )

        await interaction.response.send_message(f"💰 Withdrew **${amount}** from your bank!")


async def setup(bot):
    await bot.add_cog(Withdraw(bot))