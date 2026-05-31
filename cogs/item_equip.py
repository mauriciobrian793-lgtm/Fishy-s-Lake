import discord
from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument


class Equip(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.economy = bot.economy
        self.shop_roles = bot.shop_roles

    @app_commands.command(name="equip")
    async def equip(self, interaction: discord.Interaction, item: str):

        user = await self.economy.find_one(
            {"guild_id": str(interaction.guild.id),
             "user_id": str(interaction.user.id)}
        )

        if not user:
            return await interaction.response.send_message("❌ No user data")

        inventory = user.get("inventory", [])

        # FIX: support both strings and dict items
        owned = [i["name"] if isinstance(i, dict) else i for i in inventory]

        if item not in owned:
            return await interaction.response.send_message("❌ You don't own this item")

        shop = await self.shop_roles.find_one({"guild_id": str(interaction.guild.id)})

        if not shop:
            return await interaction.response.send_message("❌ No role mappings")

        role_id = None

        for i in shop.get("items", []):
            if i["name"] == item:
                role_id = i.get("role_id")
                break

        if not role_id:
            return await interaction.response.send_message("❌ No role assigned")

        role = interaction.guild.get_role(int(role_id))

        if not role:
            return await interaction.response.send_message("❌ Role missing")

        await interaction.user.add_roles(role)

        await interaction.response.send_message(
            f"✅ Equipped {item} → {role.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Equip(bot))