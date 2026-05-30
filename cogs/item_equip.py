import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


class Equip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop_roles = bot.shop_roles  # NEW collection

    async def get_user(self, guild_id, user_id, name):
        return await self.economy.find_one_and_update(
            {"guild_id": str(guild_id), "user_id": str(user_id)},
            {
                "$setOnInsert": {
                    "guild_id": str(guild_id),
                    "user_id": str(user_id),
                    "name": name,
                    "balance": 0,
                    "bank": 0,
                    "inventory": []
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

    @app_commands.command(name="equip", description="Equip an item to get its role")
    async def equip(self, interaction: discord.Interaction, item: str):

        if not interaction.guild:
            return await interaction.response.send_message("Guild only command.")

        user = await self.get_user(
            interaction.guild.id,
            interaction.user.id,
            interaction.user.name
        )

        inventory = user.get("inventory", [])

        # ❌ not owned
        if item not in inventory:
            return await interaction.response.send_message(
                "❌ You don't own this item."
            )

        # get role mapping
        data = await self.shop_roles.find_one({"guild_id": str(interaction.guild.id)})

        if not data or item not in data.get("items", {}):
            return await interaction.response.send_message(
                "❌ This item has no role assigned."
            )

        role_id = int(data["items"][item])
        role = interaction.guild.get_role(role_id)

        if not role:
            return await interaction.response.send_message(
                "❌ Role not found (maybe deleted)."
            )

        # give role
        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ You equipped **{item}** and received {role.mention}!",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Equip(bot))